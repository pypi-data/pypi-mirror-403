class stack():
    def __init__(self):
        self._data = []
        self._snapshots = []
    
    def __getitem__(self, index):
        return self._data[index]
    
    def __repr__(self):
        return repr(self._data)

    ### Stack Accions ###

    def push(self, item):
        self._data.insert(0, item)
        return self
    
    def drop(self, num=1):
        if self._data.__len__() == 0:
            print('Stack is empty')
        else:
            if num < 1: num = 1
            elif num > self._data.__len__(): num = self._data.__len__()
            for i in range(num):
                self._data.pop(0)
        return self
    
    def cycle(self):
        if self._data.__len__() == 0:
            print('Stack is empty')
        else:
            item = self._data[-1]
            self._data.remove(self._data[-1])
            self._data.insert(0, item)
        return self
    
    def rcycle(self):
        if self._data.__len__() == 0:
            print('Stack is empty')
        else:
            item = self._data[0]
            self._data.pop(0)
            self._data.append(item)
        return self

    def add(self, num=None):
        if num is not None and isinstance(num, (int, float)):
            item1 = self._data[0]
            self._data.pop(0)
            self._data.insert(0, item1 + num)
        else:
            if isinstance(self._data[0], (int, float)) and isinstance(self._data[1], (int, float)):
                item1 = self._data[0]
                item2 = self._data[1]
                self._data.pop(0)
                self._data.pop(0)
                self._data.insert(0, item1 + item2)
            else:
                print('Top two items are not numbers or num is not a number')
        return self
    
    def sub(self, num=None):
        if num is not None and isinstance(num, (int, float)):
            item1 = self._data[0]
            self._data.pop(0)
            self._data.insert(0, item1 - num)
        else:
            if isinstance(self._data[0], (int, float)) and isinstance(self._data[1], (int, float)):
                item1 = self._data[0]
                item2 = self._data[1]
                self._data.pop(0)
                self._data.pop(0)
                self._data.insert(0, item1 - item2)
            else:
                print('Top two items are not numbers or num is not a number')
        return self
    
    def mul(self, num=None):
        if num is not None and isinstance(num, (int, float)):
            item1 = self._data[0]
            self._data.pop(0)
            self._data.insert(0, item1 * num)
        else:
            if isinstance(self._data[0], (int, float)) and isinstance(self._data[1], (int, float)):
                item1 = self._data[0]
                item2 = self._data[1]
                self._data.pop(0)
                self._data.pop(0)
                self._data.insert(0, item1 * item2)
            else:
                print('Top two items are not numbers or num is not a number')
        return self
    
    def div(self, num=None):
        if num is not None and isinstance(num, (int, float)):
            item1 = self._data[0]
            if num != 0:
                self._data.pop(0)
                self._data.insert(0, item1 / num)
            else:
                print('Division by zero is not allowed')
        else:
            if isinstance(self._data[0], (int, float)) and isinstance(self._data[1], (int, float)):
                item1 = self._data[0]
                item2 = self._data[1]
                self._data.pop(0)
                self._data.pop(0)
                if item2 != 0:
                    self._data.insert(0, item1 / item2)
                else:
                    print('Division by zero is not allowed')
                    self._data.insert(0, item1)
                    self._data.insert(1, item2)
            else:
                print('Top two items are not integers or num is not a number')
        return self

    def res(self, num=None):
        if num is not None and isinstance(num, (int, float)):
            item1 = self._data[0]
            if num != 0:
                self._data.pop(0)
                self._data.insert(0, item1 % num)
            else:
                print('Division by zero is not allowed')
        else:
            if isinstance(self._data[0], (int, float)) and isinstance(self._data[1], (int, float)):
                item1 = self._data[0]
                item2 = self._data[1]
                self._data.pop(0)
                self._data.pop(0)
                if item2 != 0:
                    self._data.insert(0, item1 % item2)
                else:
                    print('Division by zero is not allowed')
                    self._data.insert(0, item1)
                    self._data.insert(1, item2)
            else:
                print('Top two items are not integers or num is not a number')
        return self

    def mod(self, num=None):
        if num is not None and isinstance(num, (int, float)):
            item1 = self._data[0]
            if num != 0:
                self._data.pop(0)
                self._data.insert(0, item1 % num)
            else:
                print('Division by zero is not allowed')
        else:
            if isinstance(self._data[0], (int, float)) and isinstance(self._data[1], (int, float)):
                item1 = self._data[0]
                item2 = self._data[1]
                self._data.pop(0)
                self._data.pop(0)
                if item2 != 0:
                    self._data.insert(0, item1 % item2)
                else:
                    print('Division by zero is not allowed')
                    self._data.insert(0, item1)
                    self._data.insert(1, item2)
            else:
                print('Top two items are not integers or num is not a number')
        return self
    
    def pow(self, exponent=None):
        if exponent is not None and isinstance(exponent, (int, float)):
            item1 = self._data[0]
            self._data.pop(0)
            self._data.insert(0, item1 ** exponent)
        else:
            if isinstance(self._data[0], (int, float)) and isinstance(self._data[1], (int, float)):
                item1 = self._data[0]
                item2 = self._data[1]
                self._data.pop(0)
                self._data.pop(0)
                self._data.insert(0, item1 ** item2)
            else:
                print('Top two items are not numbers or exponent is not a number')
        return self
    
    def neg(self):
        if isinstance(self._data[0], (int, float)):
            item1 = self._data[0]
            self._data.pop(0)
            self._data.insert(0, -item1)
        else:
            print('Top item is not a number')
        return self
    
    def abs(self):
        if isinstance(self._data[0], (int, float)):
            item1 = self._data[0]
            self._data.pop(0)
            self._data.insert(0, abs(item1))
        else:
            print('Top item is not a number')
        return self

    def pack(self, ammount=2):
        if ammount > self._data.__len__():
            ammount = self._data.__len__()
        items = []
        for i in range(0, ammount):
            items.append(self._data[0])
            self._data.pop(0)
        self._data.insert(0, items)
        return self

    def unpack(self):
        if isinstance(self._data[0], list):
            items = self._data[0]
            self._data.pop(0)
            for item in reversed(items):
                self._data.insert(0, item)
        else:
            print('Top item is not a list')
        return self
    
    def dup(self):
        if self._data.__len__() == 0:
            print('Stack is empty')
        else:
            item = self._data[0]
            self._data.insert(0, item)
        return self
    
    def swap(self):
        if self._data.__len__() < 2:
            print('Stack has less than two items')
        else:
            item1 = self._data[0]
            item2 = self._data[1]
            self._data[0] = item2
            self._data[1] = item1
        return self

    def rot(self):
        if self._data.__len__() < 3:
            print('Stack has less than three items')
        else:
            item1 = self._data[0]
            item2 = self._data[1]
            item3 = self._data[2]
            self._data[0] = item2
            self._data[1] = item3
            self._data[2] = item1
        return self
    
    def over(self):
        if self._data.__len__() < 2:
            print('Stack has less than two items')
        else:
            item = self._data[1]
            self._data.insert(0, item)
        return self

    ### Stack Queries ###

    def is_empty(self):
        if len(self._data) == 0:
            return True
        else:
            return False
    
    def depth(self):
        return len(self._data)

    def peek(self, index = 0):
        if index < 0 or index >= self._data.__len__():
            print('Index out of range')
        else:
            return self._data[index]

    def last(self):
        if self._data.__len__() == 0:
            print('Stack is empty')
        else:
            return self._data[-1]

### Comparasion / Logic operators ###

    def greater(self, num = None):
        if isinstance(self._data[0], (int, float)) and isinstance(num, (int, float)):
            return self._data[0] > num
        elif isinstance(self._data[0], (int, float)) and isinstance(self._data[1], (int, float)):
            return self._data[0] > self._data[1]
        else:
            print('Top item or num is not a number')
            return False
    
    def less(self, num = None):
        if isinstance(self._data[0], (int, float)) and isinstance(num, (int, float)):
            return self._data[0] < num
        elif isinstance(self._data[0], (int, float)) and isinstance(self._data[1], (int, float)):
            return self._data[0] < self._data[1]
        else:
            print('Top item or num is not a number')
            return False
    
    def equal(self, item = None):
        if item is not None:
            return self._data[0] == item
        else:
            return self._data[0] == self._data[1]
    
    def sand(self, item = None):
        if item is not None:
            if isinstance(self._data[0], (int, float)) and isinstance(item, (int, float)):
                return bool(self._data[0]) and bool(item)
            else:
                print('Top of stack or item is not a boolean value')
                return False
        else:
            if self.size() < 2:
                print('Stack has less than two items')
                return False
            elif isinstance(self._data[0], (int, float)) and isinstance(self._data[1], (int, float)):
                return bool(self._data[0]) and bool(self._data[1])
            else:
                print('Top two items are not boolean values')
                return False
    
    def sor(self, item = None):
        if item is not None:
            if isinstance(self._data[0], (int, float)) and isinstance(item, (int, float)):
                return bool(self._data[0]) or bool(item)
            else:
                print('Top of stack or item is not a boolean value')
                return False
        else:
            if self.size() < 2:
                print('Stack has less than two items')
                return False
            elif isinstance(self._data[0], (int, float)) and isinstance(self._data[1], (int, float)):
                return bool(self._data[0]) or bool(self._data[1])
            else:
                print('Top two items are not boolean values')
                return False
    
    def snot(self):
        if isinstance(self._data[0], bool):
            return not self._data[0]
        else:
            print('Top of stack is not a boolean value')
            return False
    
    def map(self, func):
        for i in range(0, self._data.__len__()):
            self._data[i] = func(self._data[i])
        return self
    
    def filter(self, func):
        filtered_data = []
        for item in self._data:
            if func(item):
                filtered_data.append(item)
        self._data = filtered_data
        return self
    
    def apply_at(self, func, index=0):
        if index < 0 or index >= self._data.__len__():
            print('Index out of range')
        else:
            self._data[index] = func(self._data[index])
        return self
    
    def map_if(self, func, filter_func):
        for i in range(0, self._data.__len__()):
            if filter_func(self._data[i]):
                self._data[i] = func(self._data[i])
        return self

### Snapshot functionality ###

    def snapshot(self):
        self._snapshots.append(self._data.copy())
        return self
    
    def restore(self):
        if self._snapshots.__len__() == 0:
            print('No snapshots to restore')
        else:
            self._data = self._snapshots.pop()
        return self