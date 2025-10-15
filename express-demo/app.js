const express = require('express');
const app = express();

app.get('/ping', (req, res) => res.send('pong'));
app.post('/upload', (req, res) => res.send('upload ok'));
app.put('/user/:id', (req, res) => res.send(`User ${req.params.id} updated`));

app.listen(3000, () => console.log('Server running on port 3000'));

