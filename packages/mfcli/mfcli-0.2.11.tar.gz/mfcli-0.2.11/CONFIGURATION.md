# mfcli Configuration Guide

Complete guide to configuring mfcli for hardware document analysis.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration Methods](#configuration-methods)
- [Required API Keys](#required-api-keys)
- [Vector Database Settings](#vector-database-settings)
- [Optional Settings](#optional-settings)
- [Configuration File Location](#configuration-file-location)
- [Validation](#validation)
- [Troubleshooting](#troubleshooting)

## Quick Start

The fastest way to configure mfcli:

```bash
mfcli configure
```

This interactive wizard will:
- Guide you through API key setup
- Provide direct links to get each key
- Validate keys automatically
- Set sensible defaults
- Save configuration to the correct location

## Configuration Methods

### Method 1: Interactive Wizard (Recommended)

```bash
# Start configuration wizard
mfcli configure

# Check existing configuration
mfcli configure --check
```

**Advantages:**
- ✅ Step-by-step guidance
- ✅ Automatic validation
- ✅ Links to get API keys
- ✅ Smart defaults
- ✅ Error prevention

### Method 2: Manual Configuration

Create/edit the `.env` file directly:

**Location:**
- Windows: `C:\Users\<username>\Multifactor\.env`
- Linux/macOS: `~/Multifactor/.env`

**Content:**
```ini
# API Keys (Required)
google_api_key=your_google_api_key
openai_api_key=your_openai_api_key
llama_cloud_api_key=your_llamaparse_api_key
digikey_client_id=your_digikey_client_id
digikey_client_secret=your_digikey_client_secret

# Vector Database Configuration
chunk_size=1000
chunk_overlap=200
embedding_model=text-embedding-3-small
embedding_dimensions=1536
```

### Method 3: Environment Variables

For advanced users or CI/CD environments:

```bash
# Set environment variables
export GOOGLE_API_KEY="your_key"
export OPENAI_API_KEY="your_key"
export LLAMA_CLOUD_API_KEY="your_key"
export DIGIKEY_CLIENT_ID="your_id"
export DIGIKEY_CLIENT_SECRET="your_secret"
```

**Note:** `.env` file takes precedence over environment variables.

## Required API Keys

### 1. Google Gemini API Key

**Purpose:** AI-powered document analysis and processing

**Get Your Key:**
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key

**Configuration:**
```ini
google_api_key=AIzaSy...
```

**Testing:**
```bash
# The configure wizard tests this automatically
# Or test manually in Python:
python -c "import google.generativeai as genai; genai.configure(api_key='YOUR_KEY'); print(list(genai.list_models())[:1])"
```

### 2. OpenAI API Key

**Purpose:** Generating embeddings for semantic search (RAG)

**Get Your Key:**
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key immediately (shown only once)

**Requirements:**
- Billing must be enabled on your OpenAI account
- Sufficient credits for embedding operations

**Configuration:**
```ini
openai_api_key=sk-proj-...
```

**Cost Estimate:**
- Embeddings are inexpensive (~$0.10 per 1M tokens)
- Typical hardware project: $0.01-$0.50 total

**Testing:**
```bash
# Test with curl
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_KEY"
```

### 3. LlamaParse API Key

**Purpose:** Advanced PDF parsing and text extraction

**Get Your Key:**
1. Visit [LlamaIndex Cloud](https://cloud.llamaindex.ai/)
2. Sign up for a free account
3. Navigate to API Keys section
4. Create a new API key

**Free Tier:**
- 7,000 pages per day
- Sufficient for most users

**Configuration:**
```ini
llama_cloud_api_key=llx-...
```

### 4. DigiKey API Credentials

**Purpose:** Automatic component datasheet downloads

**Get Your Credentials:**
1. Visit [DigiKey Developer Portal](https://developer.digikey.com/)
2. Register for a developer account
3. Create a new application
4. Note your Client ID and Client Secret

**Configuration:**
```ini
digikey_client_id=your_client_id
digikey_client_secret=your_client_secret
```

**Note:** DigiKey API requires OAuth2 flow on first use.

## Vector Database Settings

These settings control how documents are split and embedded for semantic search.

### Chunk Size

**Purpose:** Number of characters per document chunk

**Default:** 1000

**Configuration:**
```ini
chunk_size=1000
```

**Tuning Guide:**
- **Smaller (500-800)**: More precise search, more chunks
- **Medium (1000-1500)**: Balanced (recommended)
- **Larger (2000-3000)**: More context, fewer chunks

**Trade-offs:**
- Larger chunks: More context but less precise matching
- Smaller chunks: More precise but may lose context

### Chunk Overlap

**Purpose:** Number of overlapping characters between chunks

**Default:** 200

**Configuration:**
```ini
chunk_overlap=200
```

**Tuning Guide:**
- **Small (50-100)**: Minimal overlap, more distinct chunks
- **Medium (200-300)**: Balanced (recommended)
- **Large (400-500)**: Maximum context preservation

**Rule of Thumb:** 15-25% of chunk_size

### Embedding Model

**Purpose:** OpenAI model used for generating embeddings

**Default:** text-embedding-3-small

**Options:**
- `text-embedding-3-small`: Fast, cost-effective (recommended)
- `text-embedding-3-large`: Higher quality, more expensive
- `text-embedding-ada-002`: Legacy model

**Configuration:**
```ini
embedding_model=text-embedding-3-small
```

**Comparison:**

| Model | Dimensions | Speed | Cost | Quality |
|-------|------------|-------|------|---------|
| 3-small | 1536 | Fast | Low | Good |
| 3-large | 3072 | Medium | Medium | Excellent |
| ada-002 | 1536 | Fast | Low | Good |

### Embedding Dimensions

**Purpose:** Vector dimensions for embeddings

**Default:** 1536 (for text-embedding-3-small)

**Configuration:**
```ini
embedding_dimensions=1536
```

**Important:** Must match your embedding_model:
- text-embedding-3-small: 1536
- text-embedding-3-large: 3072
- text-embedding-ada-002: 1536

## Optional Settings

### AWS Configuration (Optional)

For S3 storage integration:

```ini
# AWS credentials (optional)
aws_access_key_id=AKIA...
aws_secret_access_key=...
aws_region=us-east-1
s3_bucket_name=my-hardware-docs
```

**When to use:**
- Large-scale document storage
- Team collaboration
- Cloud backup requirements

### Database Path (Optional)

Custom SQLite database location:

```ini
# Default: ./sessions.db
sqlite_db_path=/path/to/custom/database.db
```

## Configuration File Location

The configuration file is stored in a platform-specific location:

### Windows
```
C:\Users\<username>\Multifactor\.env
```

**Access:**
```powershell
# Open in notepad
notepad $env:USERPROFILE\Multifactor\.env

# View path
echo $env:USERPROFILE\Multifactor\.env
```

### Linux
```
/home/<username>/Multifactor/.env
```

**Access:**
```bash
# Edit with nano
nano ~/Multifactor/.env

# View path
ls -la ~/Multifactor/.env
```

### macOS
```
/Users/<username>/Multifactor/.env
```

**Access:**
```bash
# Edit with default editor
open -t ~/Multifactor/.env

# View path
ls -la ~/Multifactor/.env
```

## Validation

### Automatic Validation

The configuration wizard validates keys automatically:

```bash
mfcli configure
```

During setup, each API key is tested with a simple request.

### Manual Validation

Check configuration status:

```bash
# Check configuration
mfcli configure --check

# Comprehensive system check
mfcli doctor
```

### Validation Checklist

✅ **Google API Key**
- [ ] Key exists in config
- [ ] Key format is correct (starts with AIza)
- [ ] Key can list models

✅ **OpenAI API Key**
- [ ] Key exists in config
- [ ] Key format is correct (starts with sk-)
- [ ] Billing enabled on account
- [ ] Key has sufficient credits

✅ **LlamaParse API Key**
- [ ] Key exists in config
- [ ] Key format is correct (starts with llx-)
- [ ] Account has available quota

✅ **DigiKey Credentials**
- [ ] Client ID exists
- [ ] Client Secret exists
- [ ] Application is approved

## Troubleshooting

### Configuration File Not Found

**Symptom:** mfcli can't find configuration

**Solutions:**

1. **Run configuration wizard:**
   ```bash
   mfcli configure
   ```

2. **Check file location:**
   ```bash
   # Windows
   dir %USERPROFILE%\Multifactor
   
   # Linux/macOS
   ls -la ~/Multifactor
   ```

3. **Create directory if missing:**
   ```bash
   # Windows
   mkdir %USERPROFILE%\Multifactor
   
   # Linux/macOS
   mkdir -p ~/Multifactor
   ```

### API Key Invalid

**Symptom:** 401 Unauthorized or API key errors

**Solutions:**

1. **Verify key is correct:** Copy-paste carefully, no extra spaces
2. **Check key status:** Some keys expire or get revoked
3. **Billing enabled:** OpenAI requires billing
4. **Regenerate key:** Create a new one if needed

### Embedding Dimension Mismatch

**Symptom:** ChromaDB errors about dimension mismatch

**Solution:**
```bash
# Delete and rebuild ChromaDB
# Windows:
Remove-Item -Recurse -Force $env:LOCALAPPDATA\Multifactor\chromadb

# Linux/macOS:
rm -rf ~/.local/share/Multifactor/chromadb

# Then reprocess documents
mfcli run
```

### Permission Denied

**Symptom:** Can't write to configuration file

**Solutions:**

- Check file permissions
- Ensure directory exists
- On Linux/macOS: `chmod 600 ~/Multifactor/.env`
- On Windows: Check user has write access

### Configuration Not Loaded

**Symptom:** mfcli doesn't see configuration changes

**Solutions:**

1. **Verify file location is correct**
2. **Check file syntax** - no typos in key names
3. **Restart mfcli** - some changes need restart
4. **Clear any cached configs** - rerun `mfcli doctor`

### macOS SSL Certificate Error

**Symptom:** `[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate` when running `mfcli run`

**Cause:** This error occurs when Python cannot verify SSL certificates for HTTPS connections to external APIs (Google Gemini, OpenAI, etc.). **This is NOT related to environment variable case** (lowercase vs uppercase).

**Automatic Fix (v0.2.1+):**

Starting with version 0.2.1, mfcli automatically detects and attempts to fix SSL certificate issues on macOS when you run any command. Simply run any mfcli command and it will attempt the fix automatically.

If the automatic fix doesn't work, try the manual solutions below:

**Manual Solutions:**

**Option 1: Run Python's Certificate Installer (Easiest)**

```bash
# Find and run the certificate installer
/Applications/Python\ 3.12/Install\ Certificates.command
```

**Option 2: Install via Homebrew**

```bash
# If you installed Python via Homebrew
brew reinstall python@3.12
```

**Option 3: Install certifi Package**

```bash
# Install certifi in pipx environment
pipx inject mfcli certifi

# Or reinstall mfcli
pipx reinstall mfcli
```

**Option 4: Manual Installation**

```bash
# Install certifi
pip3 install --upgrade certifi

# Verify installation
python3 -c "import certifi; print(certifi.where())"
```

**Test the fix:**
```bash
# Test SSL connection
python3 -c "import ssl; import urllib.request; urllib.request.urlopen('https://www.google.com')"

# Then retry mfcli
mfcli run
```

**See also:** [INSTALL.md - macOS SSL Certificate Error](INSTALL.md#macos-ssl-certificate-error) for detailed instructions.

## Best Practices

### Security

- **Never commit `.env` files** to version control
- **Use strong API keys** - don't share them
- **Rotate keys periodically** - especially if exposed
- **Limit key permissions** - use minimum required scopes

### Organization

- **One configuration per machine** - stored in user directory
- **Document your settings** - note why you changed defaults
- **Backup your config** - especially for custom tuning

### Performance

- **Start with defaults** - they work well for most cases
- **Monitor costs** - track OpenAI API usage
- **Tune if needed** - only after testing defaults
- **Test changes** - verify improvements before keeping

## Configuration Examples

### Minimal Configuration

```ini
google_api_key=AIzaSy...
openai_api_key=sk-proj-...
llama_cloud_api_key=llx-...
digikey_client_id=your_id
digikey_client_secret=your_secret
chunk_size=1000
chunk_overlap=200
embedding_model=text-embedding-3-small
embedding_dimensions=1536
```

### High-Quality Configuration

For maximum search quality:

```ini
google_api_key=AIzaSy...
openai_api_key=sk-proj-...
llama_cloud_api_key=llx-...
digikey_client_id=your_id
digikey_client_secret=your_secret
chunk_size=1500
chunk_overlap=300
embedding_model=text-embedding-3-large
embedding_dimensions=3072
```

### Cost-Optimized Configuration

For minimal costs:

```ini
google_api_key=AIzaSy...
openai_api_key=sk-proj-...
llama_cloud_api_key=llx-...
digikey_client_id=your_id
digikey_client_secret=your_secret
chunk_size=800
chunk_overlap=150
embedding_model=text-embedding-3-small
embedding_dimensions=1536
```

## Getting Help

- **Interactive Setup**: `mfcli configure`
- **System Check**: `mfcli doctor`
- **Check Config**: `mfcli configure --check`
- **Issues**: [GitHub Issues](https://github.com/MultifactorAI/multifactor-adk-backend/issues)

## Related Documentation

- [Installation Guide](INSTALL.md)
- [MCP Setup Guide](MCP_SETUP.md)
- [Main README](README.md)

---

**Tip:** Start with the interactive wizard (`mfcli configure`) for the smoothest experience!
