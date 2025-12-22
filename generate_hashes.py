from werkzeug.security import generate_password_hash

print('RohiniGH2 (password: 123):', generate_password_hash('123'))
print('admin123 (password: 123456):', generate_password_hash('123456'))
