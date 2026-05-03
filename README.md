## Rationality
<p>
  A Reddit debate simulator that role plays as reddit users by scraping post for users and getting their comment history.
  Then they will vote on a question, debate, then vote again.
</p>

### Download Dependencies
```
python3 -m venv .venv               # make venv
source .venv/bin/activate           # activate
pip install -r requirements.txt     # download deps
```

### Running Locally
```
npm run dev                         # start dev server (inside /frontend)
fastapi dev src/main.py             # start fastapi server
```

## Preview

### 1. Configure the debate
<img width="900" alt="Input screen" src="https://github.com/user-attachments/assets/8a92a702-42dc-4539-8145-10df4ade99cd" />

### 2. Generate Reddit user agents
<img width="900" alt="User agents screen" src="https://github.com/user-attachments/assets/af073bd8-ef0c-4b1a-98c0-0703fe9fa914" />

### 3. View voting results
<img width="900" alt="Voting results screen" src="https://github.com/user-attachments/assets/eba7553d-8d33-4777-ab53-d58b9aebe3bb" />

### 4. Review the debate
<img width="900" alt="Debate results screen" src="https://github.com/user-attachments/assets/5152ccdb-6b30-4ef6-855e-0d3ac39b6533" />
