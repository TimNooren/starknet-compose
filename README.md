# Starknet Compose

I'm trying to learn about Starknet and get familiar with the Cairo programming language. This repo represents my understandings so far, mainly  regarding:
- Account abstraction (and how to use OpenZeppelin's Account contracts)
- Signature validation
- Unit testing

Deploying contracts manually quickly got boring, so built a simple tool that lets the user define contracts in a config file, and deploy those contracts in one go (similar to the starknet-hardhat-plugin). It also handles creating accounts (Account contract + key pair), and invoking other contracts through these accounts.

Next steps include:
- Adding flexibility to contract definitions; allowing dynamic references to other contracts or accounts, for instance to pass an account address as the contract owner during construction.
- Adding tests for the deployment tool itself. 

## Quickstart

Build the docker images:
```bash
$ docker-compose build
```

Start the devnet:
```bash
$ docker-compose up --detach devnet
```
All subsequent steps will target this devnet.

Create an account:
```bash
$ docker-compose run dev account create
```
This creates the account called `main` and will deploy an OpenZeppelin Account contract. If you do not specify an account for subsequent actions, the `main` account will be used.

Deploy the example contract `my_first_contract`:
```bash
$ docker-compose run dev deploy
Deployed my_first_contract to 0x054bf73c184b87bfc72c314b58317ed7abfb2c587738431ae75cacf277718d09
Transaction: 0x1
```

Call the contract:
```bash
$ docker-compose run dev call --contract my_first_contract --function get_owner
0x1234...
```
