# keyhunter

A tool to recover lost bitcoin private keys from dead hard drives.

## Usage

```bash
python3 keyhunter.py -i /dev/sdX --log ./sdX_log.log -o ./sdX_found_keys_list.txt
```

The output file lists found private keys, in base58 key WIF (wallet import format).

To import into bitcoind, use the following command for each key:

```bash
bitcoind importprivkey 5KXXXXXXXXXXXX
bitcoind getbalance
```

## Features and Limitations

* Supports both pre-2012 and post-2012 wallet keys.
* Supports logging to a file.
* Cannot find encrypted wallets.

## Credits

This project is a maintained fork of [pierce403/keyhunter](https://github.com/pierce403/keyhunter).
