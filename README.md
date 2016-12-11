# sequelspeare

The third installment in my lineage of pseudo-intelligent IRC bots is sequelspeare: a neural network chatbot using Tensorflow as the framework.
The previous bots, [Swiggityspeare](https://github.com/raidancampbell/swiggityspeare) and [Stupidspeare](https://github.com/raidancampbell/stupidspeare), had unruly development environments and no intelligence, respectively.

### Environment
Sequelspeare is written entirely in Python, and requires minimal dependencies to make for easier use:

- Python3, the code was written in 3.5
- `irc` package, installed via pip
- Tensorflow, the code was written in 0.10.0rc0
    - This should install several other dependencies such as `numpy` and `six`
    
### Usage
The code is provided with an existing Shakespeare dataset, and an optional pre-trained network.  To start using the code immediately, initialize and update the git submodule:

     git submodule init
     git submodule update

This will pull ~100MB(!) from the [pretrained network repository](https://github.com/raidancampbell/sequelspeare-pretrained-net), and place the files in `sequelspeare/savedata/sequelspeare-pretrained-net`.  
To install the files, simply copy them with:

     cp sequelspeare/savedata/sequelspeare-pretrained-net/* sequelspeare/savedata/

Alternatively, you can immediately train your own network with the shakespeare dataset with `python3 train.py`.  This does not require the git submodule.

Once you have an existing network, edit the `sequelspeare.json` file to specify the IRC parameters: nick, server, port, etc...  Once complete, start the bot with `python3 sequelspeare.py`

### Other Interfaces
A VT100 serial terminal interface was created.  Assuming the terminal is connected via serial cable, the following command *should* work:

     python3 serial_interface.py

Unfortunately, my terminal broke a couple hours into use, so this code is likely not perfect.
