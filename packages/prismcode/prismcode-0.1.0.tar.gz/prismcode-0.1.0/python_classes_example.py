# Python Classes Examples

# Basic Class
class Person:
    """A simple Person class"""
    
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def introduce(self):
        return f"Hi, I'm {self.name} and I'm {self.age} years old."
    
    def have_birthday(self):
        self.age += 1
        return f"Happy birthday! {self.name} is now {self.age} years old."


# Class with Class Variables and Methods
class BankAccount:
    """A bank account class with class and instance variables"""
    
    # Class variable - shared by all instances
    bank_name = "Python Bank"
    interest_rate = 0.02
    
    def __init__(self, account_holder, initial_balance=0):
        # Instance variables - unique to each instance
        self.account_holder = account_holder
        self.balance = initial_balance
        self.transaction_history = []
    
    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            self.transaction_history.append(f"Deposited ${amount}")
            return f"Deposited ${amount}. New balance: ${self.balance}"
        return "Invalid deposit amount"
    
    def withdraw(self, amount):
        if 0 < amount <= self.balance:
            self.balance -= amount
            self.transaction_history.append(f"Withdrew ${amount}")
            return f"Withdrew ${amount}. New balance: ${self.balance}"
        return "Insufficient funds or invalid amount"
    
    def get_balance(self):
        return f"Current balance: ${self.balance}"
    
    @classmethod
    def get_bank_info(cls):
        return f"Bank: {cls.bank_name}, Interest Rate: {cls.interest_rate * 100}%"
    
    @staticmethod
    def calculate_compound_interest(principal, rate, time):
        return principal * (1 + rate) ** time


# Inheritance Example
class Vehicle:
    """Base class for vehicles"""
    
    def __init__(self, make, model, year):
        self.make = make
        self.model = model
        self.year = year
        self.is_running = False
    
    def start(self):
        self.is_running = True
        return f"{self.make} {self.model} started"
    
    def stop(self):
        self.is_running = False
        return f"{self.make} {self.model} stopped"
    
    def get_info(self):
        return f"{self.year} {self.make} {self.model}"


class Car(Vehicle):
    """Car class inheriting from Vehicle"""
    
    def __init__(self, make, model, year, doors):
        super().__init__(make, model, year)
        self.doors = doors
    
    def honk(self):
        return "Beep beep!"
    
    def get_info(self):
        # Override parent method
        return f"{super().get_info()} ({self.doors} doors)"


class Motorcycle(Vehicle):
    """Motorcycle class inheriting from Vehicle"""
    
    def __init__(self, make, model, year, engine_size):
        super().__init__(make, model, year)
        self.engine_size = engine_size
    
    def rev_engine(self):
        return "Vroom vroom!"
    
    def get_info(self):
        return f"{super().get_info()} ({self.engine_size}cc)"


# Example usage
if __name__ == "__main__":
    # Person example
    person1 = Person("Alice", 30)
    print(person1.introduce())
    print(person1.have_birthday())
    
    # BankAccount example
    account = BankAccount("John Doe", 1000)
    print(account.get_balance())
    print(account.deposit(500))
    print(account.withdraw(200))
    print(BankAccount.get_bank_info())
    
    # Vehicle inheritance example
    car = Car("Toyota", "Camry", 2023, 4)
    motorcycle = Motorcycle("Honda", "CBR", 2023, 600)
    
    print(car.get_info())
    print(car.start())
    print(car.honk())
    
    print(motorcycle.get_info())
    print(motorcycle.start())
    print(motorcycle.rev_engine())