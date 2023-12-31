#Author: Ram Shanker
#MIT License
#Following script will create a code signing certificate. The generated certificate shall be signed by root certificate.
#2 Number file generated by the this python script can be used to sign the executable binary file.
#Provide all the necessary details in the # High Level Configuration parameter section below.

import os
import sys
import datetime
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.x509.oid import ExtensionOID
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption, pkcs12

# High Level Configuration parameters.
certificateCommonName = u"CodeSigner-01" #Generated file will have this file name.
organizationName      = u"Your Company Name" # For individual it is personal name.
organizationUnit      = u"Structural Department"
countryCode2Digit     = u"IN"
stateOrProvince       = u"New Delhi"
locality              = u"Bhikaji Kama Place"

# Root certificate details
caPublicKeyFileName   = u"RootCA-01.crt" # Remember to provide exact file name including file extension. Ex. .crt etc.
caPrivateKeyFileName  = u"RootCA-01.key"

###################################################################
# Do not change any code below this line. Only do configuration above
asymmetric_algorithm = "rsa" # It can be either "rsa" or "ed25519"

# Check safely for existing of existing certificate private key to avoid accidentally deleting / overwriting it.
script_directory = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_directory, certificateCommonName + u".key")
if os.path.isfile(file_path):
    print("A private key file with filename: " + certificateCommonName + u".key" + u" already exists.")
    print("Would you like to over-write this key with a newly generated one?")
    user_choice = input("If you choose yes,old keys will be lost forever. (yes/no): ")

    if user_choice.lower() == "no" or user_choice.lower() == "n":
        sys.exit()

# We store our private key using some password only. Ask the user for password.
password = input("Enter password of root certificate private key: ")

# Derive a key from the password
# salt is some random sequence of characters required to defend against rainbow-table attack. It can be any long sentence
salt = b'salt_thiscanbeanylargesentenceforexampleearthortatesaroundthesunandsoon'
kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=default_backend())
key = kdf.derive(password.encode())

with open(caPublicKeyFileName, "rb") as cert_file: # Read and load public key from the public.crt file
    cert_data = cert_file.read()
    root_cert = x509.load_pem_x509_certificate(cert_data, default_backend()) # Parse the certificate

with open(caPrivateKeyFileName, "rb") as private_file: # Read the private key from the private.key file
    data = private_file.read()
    ca_private_key = serialization.load_pem_private_key(data, password=key, backend=default_backend())

# Random key generation for our code-signing certificate
if asymmetric_algorithm == "ed25519":
    private_key = ed25519.Ed25519PrivateKey.generate() #Apparently windows8.1 not accepting ed25519 signature?
    hashAlgorithm = None
else: # Default fallback rsa.
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    hashAlgorithm = hashes.SHA256()

#Compute the public key corresponding to private key. crypto library automatically recognizes type of private key.
public_key = private_key.public_key()

# Certificate configurations
# Build the subject of the certificate. "subject" is basically the detail of user/organization using the certificate.
subject = x509.Name([
    x509.NameAttribute(x509.NameOID.COUNTRY_NAME, countryCode2Digit),
    x509.NameAttribute(x509.NameOID.STATE_OR_PROVINCE_NAME, stateOrProvince),
    x509.NameAttribute(x509.NameOID.LOCALITY_NAME, locality),
    x509.NameAttribute(x509.NameOID.ORGANIZATION_NAME, organizationName),
    x509.NameAttribute(x509.NameOID.ORGANIZATIONAL_UNIT_NAME, organizationUnit),
    x509.NameAttribute(x509.NameOID.COMMON_NAME, certificateCommonName)
])

builder = x509.CertificateBuilder()
builder = builder.subject_name(subject)
builder = builder.issuer_name(root_cert.subject) # For downstream certificates, issuer_name is one step above in cert chain.
one_day = datetime.timedelta(1, 0, 0)
builder = builder.not_valid_before(datetime.datetime.today() - one_day)
builder = builder.not_valid_after(datetime.datetime.today() + (one_day * 365 * 1)) # 1 Years. Intentionally keeping it short duration
builder = builder.serial_number(x509.random_serial_number())
builder = builder.public_key(public_key)

# Associate with Signer public keys.
# Generate the AuthorityKeyIdentifier using the root's SubjectKeyIdentifier
authority_key_identifier = x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
    root_cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_KEY_IDENTIFIER).value
)

#Add multiple required extensions. Sequence of extension is kept same as google-chrome-setup executable certificate extensions
builder = builder.add_extension(authority_key_identifier,critical=False) # Add the AuthorityKeyIdentifier extension
builder = builder.add_extension(x509.SubjectKeyIdentifier.from_public_key(public_key),critical=False)
# Define the Enhanced Key Usage extension = Code Signer
builder = builder.add_extension(x509.ExtendedKeyUsage([x509.OID_CODE_SIGNING]),critical=False)
# Define the Key Usage extension
key_usage = x509.KeyUsage(
    digital_signature=True, #Only this one is required for  a code-signing certificate.
    content_commitment=False,
    key_encipherment=False,
    data_encipherment=False,
    key_agreement=False,
    key_cert_sign=False, #The bit keyCertSign is for use in CA certificates only. 
    crl_sign=False,
    encipher_only=False,
    decipher_only=False
)
builder = builder.add_extension(key_usage,critical=True)
basic_constraints = x509.BasicConstraints(ca=False, path_length=None) #Declare it as end entity.
builder = builder.add_extension(basic_constraints,critical=True)

#Finally generate the certificate using all the options provided above. Note that it is signed by ca's private key.
# Algorithm must be None when signing via ed25519 or ed448. For RSA it can be hashes.SHA256()
code_signing_certificate = builder.sign(
    private_key=ca_private_key, algorithm=hashAlgorithm, backend=default_backend()
)

# Save to File after generating PEM-encoded string of the certificate object.
# Combine the end entity certificate and root certificate into a single PEM-encoded string
combined_cert = code_signing_certificate.public_bytes(serialization.Encoding.PEM) + b"\n\n" + root_cert.public_bytes(serialization.Encoding.PEM)

# Convert the private key object to a PEM-encoded string
# We store our private key using some password only. Ask the user for password.
password = input("Enter password to store private key of code-signing certificate: ")

# Derive a key from the password
# salt is some random sequence of characters required to defend against rainbow-table attack. It can be any long sentence
salt = b'salt_thiscanbeanylargesentenceforexampleearthortatesaroundthesunandsoon'
kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000, backend=default_backend())
key = kdf.derive(password.encode())

pem_data_private = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.BestAvailableEncryption(key)
)

# Write the PEM-encoded string to a file
with open(certificateCommonName + ".crt", 'wb') as file:
    file.write(combined_cert)
    
with open(certificateCommonName + ".key", 'wb') as file:
    file.write(pem_data_private)

# Windows signtool.exe accepts .pfx file only. Which incorporates both public key and private key.
# TODO: Study what happens if commonName/password is unicode characters not mappable in ascii?
password = password.encode('utf-8') #Convert from unicode to bytes

# encryption = serialization.BestAvailableEncryption(password) # BestAvailableEncryption uses AES256_SHA256 as on July 2023.
# Windows Server 2016 and Windows 10 1703 and earlier do not support importing a PFX generated using AES256_SHA256.
# https://github.com/dsccommunity/CertificateDsc/issues/153#issuecomment-413766692
# Therefor we intentionally use weaker encryption TripleDES_SHA1. If your development machine has newer version, feel free to change it.
encryption = (
    PrivateFormat.PKCS12.encryption_builder().
    kdf_rounds(50000).
    key_cert_algorithm(pkcs12.PBES.PBESv1SHA1And3KeyTripleDESCBC).
    hmac_hash(hashes.SHA1()).build(password)
)

pfx = serialization.pkcs12.serialize_key_and_certificates(
    name=organizationName.encode('utf-8'),
    key=private_key,
    cert=code_signing_certificate,
    cas=[root_cert],
    encryption_algorithm=encryption
)

with open(certificateCommonName + ".pfx", "wb") as pfx_file:
    pfx_file.write(pfx)