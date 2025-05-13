# Dash Sequence Handling in Minima

## The Issue

When using expressions with consecutive dash/minus characters in Minima, ambiguities can arise in how they're interpreted by the parser. This is especially problematic in function calls and expressions like:

```
show(a--1);
var result = a--1;
checkif(a--1) { ... }
```

The desired interpretation is usually `a - (-1)` (subtract negative 1 from a), but the parser might incorrectly interpret it, leading to syntax errors like:

```
Syntax error at line 2, column 9: missing ')'
```

## Why This Happens

The lexer correctly tokenizes `a--1` as `a`, `-`, `-1`, but due to the grammar rules of the language, the parser may expect different token patterns when there are no spaces between operators.

## Recommended Solutions

To avoid these ambiguities, use one of these clearer syntax alternatives:

### 1. Use spaces between operators (RECOMMENDED)

```
show(a - -1);
var result = a - -1;
checkif(a - -1) { ... }
```

### 2. Use parentheses

```
show(a-(-1));
var result = a-(-1);
checkif(a-(-1)) { ... }
```

### 3. Alternative equivalent expressions

```
show(a+(-1));  // Adding a negative number
var result = a+(-1);
```

## Special Cases

The following cases are handled properly and don't need special formatting:

```
a--; // Post-decrement (works as expected)
a - 1 // Simple subtraction (works as expected)
```

## Warnings

The lexer now provides helpful warnings when it encounters potentially ambiguous dash sequences:

1. Double dash with number (`a--1`):
   > Ambiguous syntax: 'a--1' will be interpreted as 'a - (-1)' but might cause parser errors. Use spaces 'a - -1' or parentheses 'a-(-1)' for clarity.

2. Triple dash (`a---1`):
   > Complex dash sequence '---' detected. Consider using spaces or parentheses for clarity.

3. Quadruple dash (`a----1`):
   > Very complex dash sequence '----' detected. Use parentheses or spaces to clearly express your intention.

These warnings help identify code that might compile but cause unexpected behavior or syntax errors. 