import subprocess

password = input("Password for MongoDB user 'measurex': ")

#Update of config files
with open('grafana/datasources/datasource.yaml', 'r') as f:
    content = f.read().replace('password: measurex', f'password: {password}')
with open('grafana/datasources/datasource.yaml', 'w') as f:
    f.write(content)

with open('coordinatorConfig.yaml', 'r') as f:
    content = f.read().replace('password: measurex', f'password: {password}')
with open('coordinatorConfig.yaml', 'w') as f:
    f.write(content)

#Starting of both mongo and grafana containers
subprocess.run(['docker-compose', 'up', '-d', '--build'])

input("Press Enter to create the MongoDB measurex user")

#Creation of measurex user on mongo
subprocess.run([
    "docker", "exec", "measure-x-mongo",
    "mongosh", "admin",
    "--eval",
    f'db.createUser({{ user: "measurex", pwd: "{password}", roles: [{{ role: "readWrite", db: "measurex" }}] }})'
])

print("MongoDB user created successfully!")
