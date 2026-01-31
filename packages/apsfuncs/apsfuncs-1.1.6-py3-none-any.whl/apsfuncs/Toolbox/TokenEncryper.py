from cryptography.fernet import Fernet

# function to print a key and encrypted token from a passed raw token 

def encrypt_token(token="", key=""):
    # If no key was given then generate a new encryption key
    if len(key) == 0:
        key = Fernet.generate_key()
        print("Key: {}".format(key.decode()))

    #  Generate the cipher object
    cipher = Fernet(key)

    # Encrypt the token
    encrypted_token = cipher.encrypt(token.encode())

    # Print the key and encrypted token
    print("Encrypted token: {}".format(encrypted_token.decode()))

if __name__ == "__main__":
    # Example usage
    encrypt_token(token="", key="")