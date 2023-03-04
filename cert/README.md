Command used to generate a self signed SSL certificate without password. Certificate to be used only for the local environment.

openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout priv_key.pem -days 3650
