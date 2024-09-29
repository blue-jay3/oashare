# OaShare: P2P File-Sharing System

## Getting Started

### Clone the repository

```bash
git clone https://github.com/yourusername/oashare.git
cd oashare
```

### Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

pip install -r requirements.txt
```

### Running the Server
The server will start on 0.0.0.0:3000.
```bash
python p2p/p2p-server.py
```

### Running the Client
Activate your virtual environment again in a new terminal.
```bash
python p2p/p2p-client.py
```
