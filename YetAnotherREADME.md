getBalance : 
```http
https://r7kxhbmiq4nk6z5olui3aga2ye0ownsp.lambda-url.ap-south-1.on.aws/?id=user2
```

transfer : 
```bash 
curl -X POST "https://hkuzejabuoy45qdnfu53ha5t340jhruw.lambda-url.ap-south-1.on.aws/" -d '{"sender": "user1", "receiver":"user2", "amount":"10"}' -H "Content-Type: application/json"
```