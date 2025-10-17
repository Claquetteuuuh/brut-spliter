# 🔐 Bruteforce Wordlist Splitter

A Python tool to split and parallelize your bruteforce attacks into faster and more efficient sub-attacks.

## 📖 Description

Bruteforce Wordlist Splitter allows you to divide a large wordlist into multiple parts and simultaneously launch several instances of your favorite bruteforce tool. This enables you to:

- **Speed up attacks** by utilizing multiple CPU cores
- **Optimize resources** with parallelism control
- **Save time** on large wordlists (rockyou.txt, etc.)
- **Stay flexible**: compatible with any bruteforce tool

## ✨ Features

- ✅ **Universal**: Compatible with john, hashcat, hydra, netexec, medusa, etc.
- ✅ **Parallelization**: Launches multiple attacks simultaneously
- ✅ **Sequential mode**: Option to execute attacks one by one
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
| `--sequential` | Execute attacks sequentially | ❌ |
| `--max-workers` | Maximum number of simultaneous parallel attacks | ❌ |

## 📚 Examples

### NetExec (formerly CrackMapExec)

```bash
# SMB bruteforce with 10 splits
python3 spliter.py -c "netexec smb 10.10.10.10 --continue-on-success --no-bruteforce -u users.txt -p <%WORDLIST%>" -w /usr/share/wordlists/rockyou.txt -s 10

# Bruteforce with a single user
python3 spliter.py -c "netexec smb 192.168.1.0/24 -u admin -p <%WORDLIST%>" -w passwords.txt -s 5
```

### Hydra

```bash
# SSH bruteforce
python3 spliter.py -c "hydra -L users.txt -P <%WORDLIST%> ssh://192.168.1.100" -w /usr/share/wordlists/rockyou.txt -s 8

# FTP bruteforce
python3 spliter.py -c "hydra -l admin -P <%WORDLIST%> ftp://10.10.10.10" -w passwords.txt -s 4
```

### John the Ripper

```bash
# Crack a hash with split wordlist
python3 spliter.py -c "john --wordlist=<%WORDLIST%> hashes.txt" -w /usr/share/wordlists/rockyou.txt -s 6

# With rules
python3 spliter.py -c "john --wordlist=<%WORDLIST%> --rules=best64 hashes.txt" -w passwords.txt -s 4
```

### Hashcat

```bash
# MD5 hash cracking
python3 spliter.py -c "hashcat -m 0 -a 0 hash.txt <%WORDLIST%>" -w /usr/share/wordlists/rockyou.txt -s 8

# NTLM hashes
python3 spliter.py -c "hashcat -m 1000 -a 0 ntlm.txt <%WORDLIST%> --force" -w passwords.txt -s 10
```

### Medusa

```bash
# RDP bruteforce
python3 spliter.py -c "medusa -h 192.168.1.100 -u admin -P <%WORDLIST%> -M rdp" -w passwords.txt -s 5

# MySQL bruteforce
python3 spliter.py -c "medusa -h 10.10.10.10 -u root -P <%WORDLIST%> -M mysql" -w rockyou.txt -s 8
```

## 🎛️ Advanced Options

### Sequential Mode

Useful if you want to limit system load or if the bruteforce tool doesn't handle parallelism well:

```bash
python3 spliter.py -c "john --wordlist=<%WORDLIST%> hash.txt" -w rockyou.txt -s 10 --sequential
```

### Limiting Parallelism

Control the number of simultaneous attacks to avoid overloading your system:

```bash
# Split into 20 but only 5 in parallel at a time
python3 spliter.py -c "netexec smb 10.10.10.10 -u admin -p <%WORDLIST%>" -w rockyou.txt -s 20 --max-workers 5
```

### Custom Placeholder

If you prefer a different placeholder than `<%WORDLIST%>`:

```bash
python3 spliter.py -c "hydra -l admin -P {WORDLIST} ssh://10.10.10.10" -w passwords.txt -s 5 -p "{WORDLIST}"
```

## 🔍 How It Works

1. **Reading the wordlist**: The tool reads your complete wordlist
2. **Splitting**: The wordlist is divided into N equal parts
3. **Creating temporary files**: Each part is saved to a temporary file
4. **Parallel execution**: Each attack is launched with its own wordlist portion
5. **Cleanup**: Temporary files are automatically deleted at the end

## 📊 Results Summary

At the end of execution, you get a complete summary:

```
======================================================================
  Attack Summary
======================================================================
[*] Total attacks: 10
[✓] Successful: 8
[✗] Failed: 2
  [✓] Attack #1: return code 0
  [✓] Attack #2: return code 0
  [✗] Attack #3: return code 1
  ...
```

## ⚠️ Limitations and Considerations

- **RAM**: The script loads the entire wordlist into memory. For very large wordlists (>1GB), ensure you have enough RAM
- **CPU Load**: Running too many parallel attacks can saturate your CPU. Use `--max-workers` to limit
- **Network**: For network attacks, too many simultaneous connections may trigger protections (rate limiting, IDS/IPS)
- **Logs**: Outputs from all attacks are mixed. For separate logs, use `--sequential` mode

## 🛡️ Legal Disclaimer

This tool is intended for educational purposes and authorized security testing only.

**Only use this tool on:**
- Your own systems
- Systems for which you have explicit written authorization
- Legal test/lab environments (HTB, THM, etc.)

Unauthorized use of this tool may be illegal in your jurisdiction. The author is not responsible for any misuse of this tool.

## 🤝 Contributing

Contributions are welcome! Feel free to:

- Open an issue to report a bug
- Submit a pull request to add features
- Improve the documentation

## 📝 License

MIT License - See the LICENSE file for more details

## 🙏 Acknowledgments

Thanks to the infosec community and all bruteforce tool developers who make this work possible.

---

**⭐ If you find this tool useful, don't forget to star it on GitHub!**