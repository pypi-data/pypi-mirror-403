# ---------- SORTING ----------

def bubble(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


def selection(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr


# ---------- TREES ----------

class Node:
    def __init__(self, data):
        self.data = data
        self.left = None
        self.right = None


def insert(root, key):
    if root is None:
        return Node(key)
    if key < root.data:
        root.left = insert(root.left, key)
    else:
        root.right = insert(root.right, key)
    return root


def inorder(root):
    if root:
        inorder(root.left)
        print(root.data, end=" ")
        inorder(root.right)


# ---------- STACK ----------

def stack_push(stack, item):
    stack.append(item)
    return stack


def stack_pop(stack):
    if not stack:
        return None
    return stack.pop()


# ---------- ONE FUNCTION TO EXPOSE EVERYTHING ----------

def all():
    globals().update({
        'bubble': bubble,
        'selection': selection,
        'Node': Node,
        'insert': insert,
        'inorder': inorder,
        'stack_push': stack_push,
        'stack_pop': stack_pop
    })
