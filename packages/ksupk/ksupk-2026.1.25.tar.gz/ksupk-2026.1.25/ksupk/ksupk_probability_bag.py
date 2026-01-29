# coding: utf-8

import random


class ProbabilityBag:
    """
    Put objects in a bag,
    assign a weight to each object,
    and take out the object with the highest weight with the highest probability.
    """

    def __init__(self, items: dict = None):
        """
        items are dict of {Object: weight, }.
        The greater the weight, the greater the chance that the item will be pulled out.
        Weight must be int (greater than zero).
        """
        if items is not None:
            assert len(items) > 0, "Number of objects in ProbabilityBag must be greater than zero"
            for k_i in items:
                assert isinstance(items[k_i], int), "Objects in ProbabilityBag must be int"
                assert items[k_i] > 0, "Object weight in ProbabilityBag must be greater than zero"
            self.d = items.copy()
        else:
            self.d = {}

    def add(self, item: object, weight: int):
        assert weight > 0
        self.d[item] = weight

    def peek(self):
        S = sum(self.d.values())
        x = random.randint(0, S-1)
        c = 0
        for item_i in self.d:
            c += self.d[item_i]
            if x < c:  # Не эффективно, нужно сразу хранить сумму, а не вес, а потом бинарным поиском
                return item_i

    def pop(self):
        x = self.peek()
        self.d.pop(x)
        return x


if __name__ == "__main__":
    # d, d_check = {"a": 5, "b": 8, "c": 2}, {"a": 0, "b": 0, "c": 0}
    d = {}
    d_check = {}
    c = random.randint(1, 100)
    for i in range(c):
        item_i = f"a{i}"
        d[item_i] = random.randint(1, 500)
        d_check[item_i] = 0
    d[f"a{c}"] = 1
    d_check[f"a{c}"] = 0

    pb = ProbabilityBag(d)
    for i in range(1000000):
        d_check[pb.peek()] += 1

    s, s_check = sum(d.values()), sum(d_check.values())
    for el_i in d:
        print(f"{el_i}: {round(d[el_i]/s*100, 2)}% ({d[el_i]}) vs {round(d_check[el_i]/s_check*100, 2)}% ({d_check[el_i]})")
