# Welcome to claim-master's source repository.

Firebase doesn't allow you to edit auth users' custom claims from the console.
The Admin SDK is the only way to edit custom claims. claim-master is a command
line tool that allows you to modify and view custom claims with simple commands.

## Usage

Since this tool uses the Firebase Admin SDK, you must have a
firebase-service-account.json file.

```shell
# View claims with an email or UID
# Must specify the firebase-service-account.json location
cm view myemail@gmail.com -k firebase-service-account.json
cm view qj82qM78GND72q98x -k firebase-service-account.json

# Set claims with an email or UID
cm set myemail@gmail.com '{"admin":true}' -k firebase-service-account.json
cm set qj82qM78GND72q98x '{"admin":true}' -k firebase-service-account.json
```

## License

GPL v3.0 or later; check the LICENSE file for details.