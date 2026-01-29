### 0. Hello!

Hi, this is the description of a countdown, plus, this countdown may be useful

### 1. What is this?

I know it's a strange name, but I ran out of ideas choosing a name!, so I chose Banana Timer

It's a timer, what's the code? Well, here is the code to use:

First, install like this

```sh, batch
pip install --index-url https://test.pypi.org/simple/ banana_timer_test
```

for the test, or

```sh, batch
pip install banana_timer
```

once it's released in PyPI, if there are updates, then run

```sh, batch
pip install -u banana_timer
```

Run this in a script

```python
from banana_timer import countdown

@countdown
def start_heavy_process():
    print("Process is now running...")

start_heavy_process()
```

I know you need a decorator but I made it via decorator

### 2. Output

If you want any help here just type `help` after running your script

Type in any duration given in the help list

### 3. Bye!

After reading this, maybe copy paste the python code and run if you installed
