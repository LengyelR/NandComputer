# NandComputer

A computer, made entirely of nand gates.
The only operation used throughout the architecture is this:

```python
    nand = lambda x, y: not (x and y)
```

Everything else is calculated by a combination of these nested nand operations.


## Wiring

The gate.py module contains the most basic operations. For example an Or gate.

```python
class Or(SimpleGate2):
    def __init__(self):
        super().__init__()
        self.nand0 = Nand()
        self.nand1 = Nand()
        self.nand2 = Nand()

    def _wiring(self):
        a = self.nand0(self.x, self.x)
        b = self.nand1(self.y, self.y)
        return self.nand2(a, b)
```      
* _wiring represents a "physical" wiring, the only valid code here are function compositions and local variables. (With some minor exceptions.)
* A variable can be used in multiple gates (symbolises how a wire would branch).

Note that, we should only use a component ONCE inside the wiring.
While technically this would work:

```python
    def _wiring(self):
        a = self.nand(self.x, self.x)
        b = self.nand(self.y, self.y)
        return self.nand(a, b)
```    
the gate changes its inputs: nand(x, x) vs nand(y, y). 
This would mean we dynamically rewire the contraption during runtime. 
The solution is to use 3 separate nand gates, and combine them.


The input, output of the components should be the integers: 0 and 1.
Arrays are acceptable, as they represent several "unnamed" variables / components. 
Looping through them is allowed, because if we unroll the loops it should abide the above 2 rules. 

Technically, anything can be allowed, as long as it statically compiles to simple function composition. (So no branching, goto statements, etc.)

## References

* The Elements of Computing Systems: Building a Modern Computer from First Principles
* http://www.simplecpudesign.com/simple_cpu_v1/index.html
* https://www.quinapalus.com/wi-index.html
