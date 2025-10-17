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
from concurrent.futures import ThreadPoolExecutor, as_completed
import signal

class WordlistSplitter:
    def __init__(self, wordlist_path, num_splits, placeholder="<%WORDLIST%>", stop_on_success=None, output_file=None):
        self.wordlist_path = Path(wordlist_path)
        self.num_splits = num_splits
        self.placeholder = placeholder
        self.stop_on_success = stop_on_success
        self.output_file = output_file
        self.temp_dir = None
        self.split_files = []
        self.processes = []
        self.success_found = False
        self.output_handle = None
        
        # Open output file if specified
        if self.output_file:
            try:
                self.output_handle = open(self.output_file, 'w', encoding='utf-8')
            except Exception as e:
                print(f"[✗] Error opening output file: {e}")
                self.output_handle = None
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def cleanup(self):
        """Clean up temporary files and processes"""
        # Terminate running processes
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                try:
                    proc.kill()
                except:
                    pass
        
        # Clear process list
        self.processes = []
        
        # Remove temporary files
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except:
                pass
    
    def split_wordlist(self):
        """Divide the wordlist into N temporary files"""
        if not self.wordlist_path.exists():
            raise FileNotFoundError(f"Wordlist not found: {self.wordlist_path}")
        
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix="bf_split_")
        
        print(f"[*] Reading wordlist: {self.wordlist_path}")
        
        # Read all lines
        with open(self.wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        lines_per_split = (total_lines + self.num_splits - 1) // self.num_splits
        
        print(f"[*] Total lines: {total_lines}")
        print(f"[*] Splitting into {self.num_splits} parts (~{lines_per_split} lines each)")
        
        # Create split files
        for i in range(self.num_splits):
            start_idx = i * lines_per_split
            end_idx = min((i + 1) * lines_per_split, total_lines)
            
            if start_idx >= total_lines:
                break
            
            split_file = os.path.join(self.temp_dir, f"wordlist_part_{i+1}.txt")
            with open(split_file, 'w', encoding='utf-8') as f:
                f.writelines(lines[start_idx:end_idx])
            
            self.split_files.append(split_file)
            print(f"[+] Created: {split_file} ({end_idx - start_idx} lines)")
        
        return self.split_files
    
    def execute_command(self, command_template, split_file, index):
        """Execute a command with a split wordlist"""
        # Replace placeholder with the split file path
        command = command_template.replace(self.placeholder, split_file)
        
        print(f"\n[*] Starting attack #{index + 1}")
        print(f"[>] Command: {command}")
        
        try:
            # Launch the process
            proc = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            self.processes.append(proc)
            
            # Display output in real-time
            for line in proc.stdout:
                print(f"[#{index + 1}] {line.rstrip()}")
                
                # Check if success string is found
                if self.stop_on_success and self.stop_on_success in line:
                    print(f"\n[!] SUCCESS STRING FOUND in attack #{index + 1}!")
                    print(f"[!] String detected: '{self.stop_on_success}'")
                    print(f"[!] Stopping all attacks...")
                    self.success_found = True
                    
                    # Terminate all running processes
                    self.cleanup()
                    break
                
                # Check if another attack found success
                if self.success_found:
                    break
            
            proc.wait()
            
            if proc.returncode == 0:
                print(f"[✓] Attack #{index + 1} completed successfully")
            else:
                print(f"[!] Attack #{index + 1} completed with code: {proc.returncode}")
            
            return index, proc.returncode
            
        except Exception as e:
            print(f"[✗] Error executing attack #{index + 1}: {e}")
            return index, -1
    
    def run_parallel(self, command_template, max_workers=None):
        """Launch all attacks in parallel"""
        if not self.split_files:
            raise RuntimeError("Wordlists have not been split. Call split_wordlist() first.")
        
        if max_workers is None:
            max_workers = min(self.num_splits, os.cpu_count() or 4)
        
        print(f"\n[*] Launching {len(self.split_files)} parallel attacks (max {max_workers} simultaneous)")
        
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
    
    def run_sequential(self, command_template):
        """Launch all attacks sequentially"""
        if not self.split_files:
            raise RuntimeError("Wordlists have not been split. Call split_wordlist() first.")
        
        print(f"\n[*] Launching {len(self.split_files)} sequential attacks")
        
        results = []
        for i, split_file in enumerate(self.split_files):
            index, returncode = self.execute_command(command_template, split_file, i)
            results.append((index, returncode))
            
            # Stop if success was found
            if self.success_found:
                print(f"[!] Stopping sequential execution due to success string found")
                break
        
        return results


def signal_handler(sig, frame):
    """Handler to interrupt cleanly with Ctrl+C"""
    print("\n[!] Interruption detected. Cleaning up...")
    sys.exit(0)


def main():
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
    
    args = parser.parse_args()
    
    # Check that placeholder is in the command
    if args.placeholder not in args.command:
        print(f"[✗] Error: The placeholder '{args.placeholder}' is not present in the command")
        print(f"[i] Provided command: {args.command}")
        sys.exit(1)
    
    # Check that number of splits is valid
    if args.split < 1:
        print("[✗] Error: Number of splits must be >= 1")
        sys.exit(1)
    
    # Handle interruption cleanly
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 70)
    print("  Bruteforce Wordlist Splitter")
    print("=" * 70)
    
    if args.looking_for:
        print(f"[!] Auto-stop enabled: will stop all attacks when '{args.looking_for}' is found")
        print()
    
    try:
        with WordlistSplitter(args.wordlist, args.split, args.placeholder, args.looking_for) as splitter:
            # Split the wordlist
            splitter.split_wordlist()
            
            # Launch attacks
            if args.sequential:
                results = splitter.run_sequential(args.command)
            else:
                results = splitter.run_parallel(args.command, args.max_workers)
            
            # Display summary
            print("\n" + "=" * 70)
            print("  Attack Summary")
            print("=" * 70)
            
            if splitter.success_found:
                print(f"[!] ALL ATTACKS STOPPED - Success string '{args.looking_for}' was found!")
                print()
            
            success_count = sum(1 for _, rc in results if rc == 0)
            failed_count = len(results) - success_count
            
            print(f"[*] Total attacks: {len(results)}")
            print(f"[✓] Successful: {success_count}")
            print(f"[✗] Failed: {failed_count}")
            
            for index, returncode in sorted(results):
                status = "✓" if returncode == 0 else "✗"
                print(f"  [{status}] Attack #{index + 1}: return code {returncode}")
    
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[✗] Error: {e}")
        sys.exit(1)
    
    print("\n[*] Done!")


if __name__ == "__main__":
    main()