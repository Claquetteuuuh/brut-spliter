# 🔐 Bruteforce Wordlist Splitter

A Python tool to split and parallelize your bruteforce attacks into faster and more efficient sub-attacks.

## 📖 Description

Bruteforce Wordlist Splitter allows you to divide a large wordlist into multiple parts and simultaneously launch several instances of your favorite bruteforce tool. This enables you to:

- **Speed up attacks** by utilizing multiple CPU cores
- **Optimize resources** with parallelism control
- **Save time** on large wordlists (rockyou.txt, etc.)
- **Auto-stop on success** when credentials are found
- **Log everything** to a file for later analysis
- **Stay flexible**: compatible with any bruteforce tool

## ✨ Features

- ✅ **Universal**: Compatible with john, hashcat, hydra, netexec, medusa, etc.
- ✅ **Parallelization**: Launches multiple attacks simultaneously
- ✅ **Sequential mode**: Option to execute attacks one by one
- ✅ **Auto-stop**: Stops all attacks when a success string is detected
- ✅ **Output logging**: Save all execution output to a file
- ✅ **Clean management**: Automatic cleanup of temporary files
- ✅ **Safe interruption**: Ctrl+C properly stops all processes
- ✅ **Real-time output**: Displays results as they come
- ✅ **Customizable placeholder**: Adapt it to your needs

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/your-username/bruteforce-wordlist-splitter.git
cd bruteforce-wordlist-splitter

# Make the script executable
chmod +x spliter.py
```

**Requirements**: Python 3.6+

## 💻 Usage

### Basic syntax

```bash
python3 spliter.py -c "COMMAND <%WORDLIST%>" -w WORDLIST -s NUMBER_OF_SPLITS
```

### Parameters

| Parameter | Description | Required |
|-----------|-------------|----------|
| `-c, --command` | Command to execute with `<%WORDLIST%>` as placeholder | ✅ |
| `-w, --wordlist` | Path to the wordlist to split | ✅ |
| `-s, --split` | Number of parts to create | ✅ |
| `-p, --placeholder` | Custom placeholder (default: `<%WORDLIST%>`) | ❌ |
| `-lf, --looking-for` | Stop all attacks when this string is found (e.g., "STATUS_LOGON_SUCCESS") | ❌ |
| `-o, --output` | Save all output to a file (e.g., "output.txt") | ❌ |
| `--sequential` | Execute attacks sequentially instead of in parallel | ❌ |
| `--max-workers` | Maximum number of simultaneous parallel attacks | ❌ |

## 📚 Examples

### NetExec (formerly CrackMapExec)

```bash
# SMB bruteforce with 10 splits
python3 spliter.py -c "netexec smb 10.10.10.10 --continue-on-success --no-bruteforce -u users.txt -p <%WORDLIST%>" -w /usr/share/wordlists/rockyou.txt -s 10

# Auto-stop when login succeeds
python3 spliter.py -c "netexec smb 192.168.1.0/24 -u admin -p <%WORDLIST%>" -w passwords.txt -s 5 -lf "STATUS_LOGON_SUCCESS"

# Save output to file
python3 spliter.py -c "netexec smb 10.10.10.10 -u users.txt -p <%WORDLIST%>" -w rockyou.txt -s 8 -o netexec_results.txt

# Combine auto-stop and logging
python3 spliter.py -c "netexec smb 10.10.10.10 -u admin -p <%WORDLIST%>" -w passwords.txt -s 10 -lf "STATUS_LOGON_SUCCESS" -o output.txt
```

### Hydra

```bash
# SSH bruteforce
python3 spliter.py -c "hydra -L users.txt -P <%WORDLIST%> ssh://192.168.1.100" -w /usr/share/wordlists/rockyou.txt -s 8

# FTP bruteforce with auto-stop
python3 spliter.py -c "hydra -l admin -P <%WORDLIST%> ftp://10.10.10.10" -w passwords.txt -s 4 -lf "password:"

# RDP with output logging
python3 spliter.py -c "hydra -l administrator -P <%WORDLIST%> rdp://192.168.1.50" -w rockyou.txt -s 6 -o hydra_rdp.txt
```

### John the Ripper

```bash
# Crack a hash with split wordlist
python3 spliter.py -c "john --wordlist=<%WORDLIST%> hashes.txt" -w /usr/share/wordlists/rockyou.txt -s 6

# With rules and logging
python3 spliter.py -c "john --wordlist=<%WORDLIST%> --rules=best64 hashes.txt" -w passwords.txt -s 4 -o john_output.txt

# Auto-stop when hash is cracked
python3 spliter.py -c "john --wordlist=<%WORDLIST%> hash.txt" -w rockyou.txt -s 8 -lf "cracked"
```

### Hashcat

```bash
# MD5 hash cracking
python3 spliter.py -c "hashcat -m 0 -a 0 hash.txt <%WORDLIST%>" -w /usr/share/wordlists/rockyou.txt -s 8

# NTLM hashes with auto-stop
python3 spliter.py -c "hashcat -m 1000 -a 0 ntlm.txt <%WORDLIST%> --force" -w passwords.txt -s 10 -lf "Cracked"

# SHA256 with logging
python3 spliter.py -c "hashcat -m 1400 -a 0 sha256.txt <%WORDLIST%>" -w rockyou.txt -s 12 -o hashcat_results.txt
```

### Medusa

```bash
# MySQL bruteforce
python3 spliter.py -c "medusa -h 10.10.10.10 -u root -P <%WORDLIST%> -M mysql" -w rockyou.txt -s 8

# SSH with auto-stop and logging
python3 spliter.py -c "medusa -h 192.168.1.100 -u admin -P <%WORDLIST%> -M ssh" -w passwords.txt -s 5 -lf "SUCCESS" -o medusa_ssh.txt
```

## 🎛️ Advanced Options

### Auto-stop on Success

Stop all attacks immediately when a success string is detected in the output:

```bash
# NetExec - stops when login succeeds
python3 spliter.py -c "netexec smb 10.10.10.10 -u users.txt -p <%WORDLIST%>" \
  -w rockyou.txt -s 10 -lf "STATUS_LOGON_SUCCESS"

# Hydra - stops when password is found
python3 spliter.py -c "hydra -l admin -P <%WORDLIST%> ssh://10.10.10.10" \
  -w passwords.txt -s 8 -lf "password:"

# Custom success indicator
python3 spliter.py -c "custom_tool --wordlist <%WORDLIST%>" \
  -w wordlist.txt -s 5 -lf "FOUND"
```

### Output Logging

Save all execution output (commands, results, summary) to a file:

```bash
# Basic logging
python3 spliter.py -c "netexec smb 10.10.10.10 -u admin -p <%WORDLIST%>" \
  -w passwords.txt -s 5 -o results.txt

# Combine with auto-stop
python3 spliter.py -c "hydra -l admin -P <%WORDLIST%> ssh://10.10.10.10" \
  -w rockyou.txt -s 10 -lf "password:" -o hydra_output.txt
```

The output file will contain:
- All commands executed
- Real-time output from each attack instance
- Success/failure messages
- Final summary with statistics

### Sequential Mode

Execute attacks one at a time instead of in parallel:

```bash
python3 spliter.py -c "john --wordlist=<%WORDLIST%> hash.txt" \
  -w rockyou.txt -s 10 --sequential
```

Useful when:
- You want to limit system load
- The tool doesn't handle parallelism well
- You need cleaner, non-mixed output

### Limiting Parallelism

Control the number of simultaneous attacks:

```bash
# Split into 20 but only 5 run at once
python3 spliter.py -c "netexec smb 10.10.10.10 -u admin -p <%WORDLIST%>" \
  -w rockyou.txt -s 20 --max-workers 5
```

### Custom Placeholder

Use a different placeholder than `<%WORDLIST%>`:

```bash
python3 spliter.py -c "hydra -l admin -P {WORDLIST} ssh://10.10.10.10" \
  -w passwords.txt -s 5 -p "{WORDLIST}"
```

## 🔍 How It Works

1. **Reading the wordlist**: The tool reads your complete wordlist
2. **Splitting**: The wordlist is divided into N equal parts
3. **Creating temporary files**: Each part is saved to a temporary file in `/tmp`
4. **Parallel execution**: Each attack is launched with its own wordlist portion
5. **Real-time monitoring**: Output is displayed and optionally logged
6. **Auto-stop detection**: If enabled, monitors for success strings
7. **Cleanup**: Temporary files are automatically deleted at the end

## 📊 Results Summary

At the end of execution, you get a complete summary:

```
======================================================================
  Attack Summary
======================================================================
[!] ALL ATTACKS STOPPED - Success string 'STATUS_LOGON_SUCCESS' was found!

[*] Total attacks: 10
[✓] Successful: 8
[✗] Failed: 2
  [✓] Attack #1: return code 0
  [✓] Attack #2: return code 0
  [✗] Attack #3: return code 1
  ...

[*] Done!
[*] Output saved to: results.txt
```

## 🎯 Real-World Scenarios

### Scenario 1: Password Spray Attack

```bash
# Test common passwords against multiple users
python3 spliter.py \
  -c "netexec smb 10.10.10.0/24 -u users.txt -p <%WORDLIST%> --continue-on-success" \
  -w common_passwords.txt \
  -s 5 \
  -lf "STATUS_LOGON_SUCCESS" \
  -o password_spray_results.txt
```

### Scenario 2: Hash Cracking Competition

```bash
# Crack hashes as fast as possible
python3 spliter.py \
  -c "hashcat -m 1000 -a 0 ntlm_hashes.txt <%WORDLIST%> --force" \
  -w /usr/share/wordlists/rockyou.txt \
  -s 16 \
  -lf "Cracked" \
  -o hashcat_session.txt
```

### Scenario 3: SSH Bruteforce with Resource Limits

```bash
# Limit to 3 simultaneous connections to avoid detection
python3 spliter.py \
  -c "hydra -l admin -P <%WORDLIST%> ssh://192.168.1.100 -t 4" \
  -w passwords.txt \
  -s 10 \
  --max-workers 3 \
  -lf "password:" \
  -o ssh_bruteforce.log
```

## ⚠️ Limitations and Considerations

- **RAM**: The script loads the entire wordlist into memory. For very large wordlists (>1GB), ensure you have enough RAM
- **CPU Load**: Running too many parallel attacks can saturate your CPU. Use `--max-workers` to limit
- **Network**: For network attacks, too many simultaneous connections may trigger protections (rate limiting, IDS/IPS)
- **Logs**: In parallel mode, outputs from all attacks are mixed. Use `--sequential` for cleaner logs or use `-o` to save everything
- **Detection**: Multiple parallel connections to the same target may trigger security alerts

## 💡 Tips and Best Practices

1. **Start small**: Test with a small split number first (2-4) to ensure everything works
2. **Monitor resources**: Use `htop` or `top` to watch CPU/RAM usage
3. **Network attacks**: Limit parallelism with `--max-workers` to avoid overwhelming targets
4. **Use auto-stop**: Always use `-lf` for credential attacks to save time and resources
5. **Log everything**: Use `-o` for important attacks to have a record
6. **Clean wordlists**: Remove duplicates and empty lines from wordlists before splitting
7. **Combine with tools**: Use with `tmux` or `screen` for long-running attacks

## 🛡️ Legal Disclaimer

This tool is intended for educational purposes and authorized security testing only.

**Only use this tool on:**
- Your own systems
- Systems for which you have explicit written authorization
- Legal test/lab environments (HTB, THM, etc.)

Unauthorized use of this tool may be illegal in your jurisdiction. The author is not responsible for any misuse of this tool.

**Remember:**
- Always obtain proper authorization before testing
- Respect rate limits and avoid DoS conditions
- Follow responsible disclosure practices
- Comply with all applicable laws and regulations

## 🤝 Contributing

Contributions are welcome! Feel free to:

- Open an issue to report a bug
- Submit a pull request to add features
- Improve the documentation
- Share your use cases and examples

### Development Ideas

- [ ] Add support for distributed attacks across multiple machines
- [ ] Implement resume functionality for interrupted attacks
- [ ] Add progress bars for each attack instance
- [ ] Support for custom output formats (JSON, CSV)
- [ ] Integration with password cracking frameworks

## 📝 License

MIT License - See the LICENSE file for more details

## 🙏 Acknowledgments

Thanks to the infosec community and all bruteforce tool developers who make this work possible:

- **NetExec/CrackMapExec** - Network service bruteforcing
- **Hydra** - Fast network logon cracker
- **John the Ripper** - Password cracking
- **Hashcat** - Advanced password recovery
- **Medusa** - Parallel network login brute-forcer

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/your-username/bruteforce-wordlist-splitter/issues) page
2. Read through the examples in this README
3. Open a new issue with detailed information about your problem

## 📈 Changelog

### v1.1.0
- ✨ Added auto-stop feature (`-lf` / `--looking-for`)
- ✨ Added output logging (`-o` / `--output`)
- 🐛 Fixed process cleanup on interruption
- 📝 Improved documentation with real-world examples

### v1.0.0
- 🎉 Initial release
- ✅ Basic wordlist splitting
- ✅ Parallel and sequential execution modes
- ✅ Support for all major bruteforce tools

---

**⭐ If you find this tool useful, don't forget to star it on GitHub!**

**Made with ❤️ for the cybersecurity community**