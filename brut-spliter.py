#!/usr/bin/env python3
"""
Bruteforce Wordlist Splitter
Tool to split bruteforce attacks into multiple parallel sub-attacks
Compatible with john, hashcat, netexec, hydra, etc.
"""

import argparse
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Tuple, Optional, TextIO
from concurrent.futures import ThreadPoolExecutor, as_completed
import signal

class WordlistSplitter:
    def __init__(
        self, 
        wordlist_path: str, 
        num_splits: int, 
        placeholder: str = "<%WORDLIST%>", 
        stop_on_success: Optional[str] = None, 
        output_file: Optional[str] = None
    ) -> None:
        self.wordlist_path = Path(wordlist_path)
        self.num_splits = num_splits
        self.placeholder = placeholder
        self.stop_on_success = stop_on_success
        self.output_file = output_file
        self.temp_dir: Optional[str] = None
        self.split_files: List[str] = []
        self.processes: List[subprocess.Popen] = []
        self.success_found = False
        self.output_handle: Optional[TextIO] = None
        
        self._open_output_file()
        
    def _open_output_file(self) -> None:
        """Open output file if specified"""
        if self.output_file:
            try:
                self.output_handle = open(self.output_file, 'w', encoding='utf-8')
            except Exception as e:
                self.log(f"[✗] Error opening output file: {e}")
                self.output_handle = None
        
    def __enter__(self) -> 'WordlistSplitter':
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.cleanup()
        self._close_output_file()
    
    def _close_output_file(self) -> None:
        """Close output file if open"""
        if self.output_handle is not None:
            try:
                self.output_handle.close()
            except IOError as e:
                self.log(f"[!] Warning: Failed to close output file: {e}")
    
    def log(self, message: str) -> None:
        """Print message to console and optionally to output file"""
        print(message)
        if self.output_handle is not None:
            try:
                self.output_handle.write(message + '\n')
                self.output_handle.flush()
            except IOError as e:
                print(f"[!] Warning: Failed to write to output file: {e}")
    
    def cleanup(self) -> None:
        """Clean up temporary files and processes"""
        self._terminate_processes()
        self._remove_temp_files()
    
    def _terminate_processes(self) -> None:
        """Terminate all running processes"""
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                    self.log(f"[!] Warning: Process had to be forcefully killed")
                except Exception as e:
                    self.log(f"[!] Warning: Failed to kill process: {e}")
            except Exception as e:
                self.log(f"[!] Warning: Failed to terminate process: {e}")
        
        self.processes = []
    
    def _remove_temp_files(self) -> None:
        """Remove temporary directory and files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                self.log(f"[!] Warning: Failed to remove temporary files: {e}")
    
    def split_wordlist(self) -> List[str]:
        """Divide the wordlist into N temporary files using round-robin distribution"""
        if not self.wordlist_path.exists():
            raise FileNotFoundError(f"Wordlist not found: {self.wordlist_path}")
        
        self.temp_dir = tempfile.mkdtemp(prefix="bf_split_")
        
        self.log(f"[*] Reading wordlist: {self.wordlist_path}")
        
        total_lines = self._count_lines()
        self.log(f"[*] Total lines: {total_lines}")
        self.log(f"[*] Splitting into {self.num_splits} parts using round-robin distribution")
        
        self._create_split_files()
        self._distribute_lines()
        self._display_split_stats()
        
        return self.split_files
    
    def _count_lines(self) -> int:
        """Count total lines in wordlist"""
        with open(self.wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    
    def _create_split_files(self) -> None:
        """Initialize split file paths"""
        if self.temp_dir is None:
            raise RuntimeError("Temporary directory not initialized")
            
        for i in range(self.num_splits):
            split_file = os.path.join(self.temp_dir, f"wordlist_part_{i+1}.txt")
            self.split_files.append(split_file)
    
    def _distribute_lines(self) -> None:
        """Distribute wordlist lines using round-robin"""
        split_handles = [open(f, 'w', encoding='utf-8') for f in self.split_files]
        
        try:
            with open(self.wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                for idx, line in enumerate(f):
                    split_index = idx % self.num_splits
                    split_handles[split_index].write(line)
        finally:
            for handle in split_handles:
                handle.close()
    
    def _display_split_stats(self) -> None:
        """Display statistics for each split file"""
        for i, split_file in enumerate(self.split_files):
            lines_count = self._count_file_lines(split_file)
            self.log(f"[+] Created: {split_file} ({lines_count} lines)")
    
    def _count_file_lines(self, filepath: str) -> int:
        """Count lines in a file"""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return sum(1 for _ in f)
    
    def execute_command(self, command_template: str, split_file: str, index: int) -> Tuple[int, int]:
        """Execute a command with a split wordlist"""
        command = command_template.replace(self.placeholder, split_file)
        
        self.log(f"\n[*] Starting attack #{index + 1}")
        self.log(f"[>] Command: {command}")
        
        try:
            proc = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            self.processes.append(proc)
            
            return self._monitor_process_output(proc, index)
            
        except Exception as e:
            self.log(f"[✗] Error executing attack #{index + 1}: {e}")
            return index, -1
    
    def _monitor_process_output(self, proc: subprocess.Popen, index: int) -> Tuple[int, int]:
        """Monitor process output and check for success string"""
        if proc.stdout is None:
            self.log(f"[!] Warning: No stdout available for attack #{index + 1}")
            return index, -1
            
        for line in proc.stdout:
            output_line = f"[#{index + 1}] {line.rstrip()}"
            self.log(output_line)
            
            if self._check_success_string(line, index):
                break
            
            if self.success_found:
                break
        
        proc.wait()
        self._log_completion_status(index, proc.returncode)
        
        return index, proc.returncode
    
    def _check_success_string(self, line: str, index: int) -> bool:
        """Check if success string is found in output line"""
        if self.stop_on_success and self.stop_on_success in line:
            self.log(f"\n[!] SUCCESS STRING FOUND in attack #{index + 1}!")
            self.log(f"[!] String detected: '{self.stop_on_success}'")
            self.log(f"[!] Stopping all attacks...")
            self.success_found = True
            self.cleanup()
            return True
        return False
    
    def _log_completion_status(self, index: int, returncode: int) -> None:
        """Log attack completion status"""
        if returncode == 0:
            self.log(f"[✓] Attack #{index + 1} completed successfully")
        else:
            self.log(f"[!] Attack #{index + 1} completed with code: {returncode}")
    
    def run_parallel(self, command_template: str, max_workers: Optional[int] = None) -> List[Tuple[int, int]]:
        """Launch all attacks in parallel"""
        if not self.split_files:
            raise RuntimeError("Wordlists have not been split. Call split_wordlist() first.")
        
        if max_workers is None:
            max_workers = min(self.num_splits, os.cpu_count() or 4)
        
        self.log(f"\n[*] Launching {len(self.split_files)} parallel attacks (max {max_workers} simultaneous)")
        
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.execute_command, command_template, split_file, i): i
                for i, split_file in enumerate(self.split_files)
            }
            
            for future in as_completed(futures):
                index, returncode = future.result()
                results.append((index, returncode))
        
        return results
    
    def run_sequential(self, command_template: str) -> List[Tuple[int, int]]:
        """Launch all attacks sequentially"""
        if not self.split_files:
            raise RuntimeError("Wordlists have not been split. Call split_wordlist() first.")
        
        self.log(f"\n[*] Launching {len(self.split_files)} sequential attacks")
        
        results = []
        for i, split_file in enumerate(self.split_files):
            index, returncode = self.execute_command(command_template, split_file, i)
            results.append((index, returncode))
            
            if self.success_found:
                self.log(f"[!] Stopping sequential execution due to success string found")
                break
        
        return results


def signal_handler(sig: int, frame) -> None:
    """Handler to interrupt cleanly with Ctrl+C"""
    print("\n[!] Interruption detected. Cleaning up...")
    sys.exit(0)


def display_header() -> None:
    """Display application header"""
    print("=" * 70)
    print("  Bruteforce Wordlist Splitter")
    print("=" * 70)


def display_config(args: argparse.Namespace) -> None:
    """Display configuration information"""
    if args.looking_for:
        print(f"[!] Auto-stop enabled: will stop all attacks when '{args.looking_for}' is found")
    
    if args.output:
        print(f"[!] Output will be saved to: {args.output}")
        
    if args.looking_for or args.output:
        print()


def display_summary(
    splitter: WordlistSplitter, 
    results: List[Tuple[int, int]], 
    args: argparse.Namespace
) -> None:
    """Display attack summary"""
    print("\n" + "=" * 70)
    print("  Attack Summary")
    print("=" * 70)
    
    if splitter.success_found:
        msg = f"[!] ALL ATTACKS STOPPED - Success string '{args.looking_for}' was found!"
        print(msg)
        if splitter.output_handle is not None:
            splitter.output_handle.write(msg + '\n')
        print()
    
    success_count = sum(1 for _, rc in results if rc == 0)
    failed_count = len(results) - success_count
    
    summary_lines = [
        f"[*] Total attacks: {len(results)}",
        f"[✓] Successful: {success_count}",
        f"[✗] Failed: {failed_count}"
    ]
    
    for line in summary_lines:
        print(line)
        if splitter.output_handle is not None:
            splitter.output_handle.write(line + '\n')
    
    for index, returncode in sorted(results):
        status = "✓" if returncode == 0 else "✗"
        line = f"  [{status}] Attack #{index + 1}: return code {returncode}"
        print(line)
        if splitter.output_handle is not None:
            splitter.output_handle.write(line + '\n')


def validate_arguments(args: argparse.Namespace) -> None:
    """Validate command line arguments"""
    if args.placeholder not in args.command:
        print(f"[✗] Error: The placeholder '{args.placeholder}' is not present in the command")
        print(f"[i] Provided command: {args.command}")
        sys.exit(1)
    
    if args.split < 1:
        print("[✗] Error: Number of splits must be >= 1")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split bruteforce attacks into multiple parallel sub-attacks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  
  # NetExec SMB bruteforce
  %(prog)s -c "netexec smb 10.10.10.10 -u users.txt -p <%WORDLIST%>" -w passwords.txt -s 10
  
  # Hydra SSH bruteforce
  %(prog)s -c "hydra -L users.txt -P <%WORDLIST%> ssh://192.168.1.100" -w rockyou.txt -s 5
  
  # John the Ripper
  %(prog)s -c "john --wordlist=<%WORDLIST%> hash.txt" -w wordlist.txt -s 8
  
  # Hashcat
  %(prog)s -c "hashcat -m 0 -a 0 hash.txt <%WORDLIST%>" -w passwords.txt -s 4
  
  # Sequential mode (one attack at a time)
  %(prog)s -c "netexec smb 10.10.10.10 -u admin -p <%WORDLIST%>" -w pass.txt -s 5 --sequential
  
  # Auto-stop when success string is found
  %(prog)s -c "netexec smb 10.10.10.10 -u users.txt -p <%WORDLIST%>" -w pass.txt -s 10 -lf "STATUS_LOGON_SUCCESS"
  
  # Save all output to a file
  %(prog)s -c "hydra -L users.txt -P <%WORDLIST%> ssh://10.10.10.10" -w rockyou.txt -s 5 -o output.txt
  
  # Combine auto-stop and output file
  %(prog)s -c "netexec smb 10.10.10.10 -u admin -p <%WORDLIST%>" -w pass.txt -s 8 -lf "SUCCESS" -o results.txt
        """
    )
    
    parser.add_argument(
        '-c', '--command',
        required=True,
        help='Command to execute (use <%WORDLIST%> as placeholder)'
    )
    
    parser.add_argument(
        '-w', '--wordlist',
        required=True,
        help='Path to the wordlist to split'
    )
    
    parser.add_argument(
        '-s', '--split',
        type=int,
        required=True,
        help='Number of splits to create'
    )
    
    parser.add_argument(
        '-p', '--placeholder',
        default='<%WORDLIST%>',
        help='Placeholder to replace in command (default: <%WORDLIST%>)'
    )
    
    parser.add_argument(
        '--sequential',
        action='store_true',
        help='Execute attacks sequentially instead of in parallel'
    )
    
    parser.add_argument(
        '--max-workers',
        type=int,
        help='Maximum number of simultaneous parallel attacks'
    )
    
    parser.add_argument(
        '-lf', '--looking-for',
        help='Stop all attacks when this string is found in output (e.g., "STATUS_LOGON_SUCCESS")'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Save all output to a file (e.g., "output.txt")'
    )
    
    args = parser.parse_args()
    
    validate_arguments(args)
    signal.signal(signal.SIGINT, signal_handler)
    
    display_header()
    display_config(args)
    
    try:
        with WordlistSplitter(args.wordlist, args.split, args.placeholder, args.looking_for, args.output) as splitter:
            splitter.split_wordlist()
            
            if args.sequential:
                results = splitter.run_sequential(args.command)
            else:
                results = splitter.run_parallel(args.command, args.max_workers)
            
            display_summary(splitter, results, args)
    
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[✗] Error: {e}")
        sys.exit(1)
    
    print("\n[*] Done!")
    
    if args.output:
        print(f"[*] Output saved to: {args.output}")


if __name__ == "__main__":
    main()