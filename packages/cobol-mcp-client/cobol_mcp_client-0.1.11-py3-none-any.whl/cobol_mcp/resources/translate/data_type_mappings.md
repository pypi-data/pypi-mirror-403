# Complete COBOL to Java Data Type Mappings

## Numeric Types

### Basic Numeric (DISPLAY)

| COBOL PIC Clause | Java Type | Example |
|------------------|-----------|---------|
| `PIC 9` | `int` | Single digit 0-9 |
| `PIC 9(4)` | `int` | 0-9999 |
| `PIC 9(9)` | `int` | Up to 999,999,999 |
| `PIC 9(10)` to `PIC 9(18)` | `long` | Larger integers |
| `PIC S9(n)` | `int` or `long` | Signed integer |
| `PIC 9(n)V9(m)` | `BigDecimal` | Implied decimal |
| `PIC S9(n)V9(m)` | `BigDecimal` | Signed with decimal |

### Binary/Computational

| COBOL Usage | Size | Java Type |
|-------------|------|-----------|
| `COMP` / `BINARY` PIC 9(1)-9(4) | 2 bytes | `short` |
| `COMP` / `BINARY` PIC 9(5)-9(9) | 4 bytes | `int` |
| `COMP` / `BINARY` PIC 9(10)-9(18) | 8 bytes | `long` |
| `COMP-1` | 4 bytes | `float` (avoid for financial) |
| `COMP-2` | 8 bytes | `double` (avoid for financial) |
| `COMP-3` (packed decimal) | varies | `BigDecimal` |
| `COMP-4` | same as COMP | `int` or `long` |
| `COMP-5` (native binary) | varies | `int` or `long` |

### Packed Decimal (COMP-3) Storage

```
PIC S9(n) COMP-3 storage = (n + 2) / 2 bytes

Examples:
PIC S9(3) COMP-3  = 2 bytes
PIC S9(5) COMP-3  = 3 bytes
PIC S9(7) COMP-3  = 4 bytes
PIC S9(9) COMP-3  = 5 bytes
```

## Alphanumeric Types

| COBOL PIC Clause | Java Type | Notes |
|------------------|-----------|-------|
| `PIC X` | `char` or `String` | Single character |
| `PIC X(n)` | `String` | Fixed-width string |
| `PIC A(n)` | `String` | Alphabetic only |
| `PIC 9(n)` (when used as text) | `String` | Numeric characters |

### String Padding Behavior

COBOL strings are fixed-width, left-justified, space-padded:

```java
// COBOL: 05 WS-NAME PIC X(20) VALUE 'JOHN'.
// Storage: "JOHN                " (16 trailing spaces)

public class CobolString {
    private final int length;
    private String value;

    public void setValue(String s) {
        if (s.length() >= length) {
            this.value = s.substring(0, length);
        } else {
            this.value = String.format("%-" + length + "s", s);
        }
    }

    public String getValue() {
        return value;
    }

    public String getTrimmedValue() {
        return value.trim();
    }
}
```

## Special Numeric Formats

### Edited Numeric (Display Only)

| COBOL Edit Pattern | Meaning | Example Output |
|--------------------|---------|----------------|
| `PIC Z(4)9` | Zero suppress | "   12" |
| `PIC $(5)9.99` | Currency | "$   12.50" |
| `PIC -(4)9.99` | Signed | "-  12.50" |
| `PIC 9(3).9(2)` | Decimal point | "012.50" |
| `PIC 9(3),9(3)` | Comma insertion | "001,234" |

For edited fields, store the raw value in Java and format only for display:

```java
private BigDecimal amount;

public String formatForDisplay() {
    return String.format("%,.2f", amount);
}
```

## Arrays (OCCURS)

### Fixed-Size Arrays

```cobol
01 WS-TABLE.
   05 WS-ITEM OCCURS 10 TIMES PIC X(20).
```

```java
// Option 1: Array
private String[] wsItem = new String[10];

// Option 2: List (if size may vary)
private List<String> wsItem = new ArrayList<>(10);
```

### Indexed Arrays (OCCURS INDEXED BY)

```cobol
01 WS-TABLE.
   05 WS-ITEM OCCURS 100 TIMES INDEXED BY WS-IDX.
      10 ITEM-CODE PIC X(5).
      10 ITEM-QTY  PIC 9(5).
```

```java
public class WsItem {
    private String itemCode;
    private int itemQty;
}

private WsItem[] wsTable = new WsItem[100];
private int wsIdx; // COBOL indexes are 1-based!

// COBOL SET WS-IDX TO 5 → wsIdx = 4 (convert to 0-based)
```

### Variable-Length Arrays (OCCURS DEPENDING ON)

```cobol
01 WS-TABLE.
   05 WS-COUNT PIC 9(3).
   05 WS-ITEM OCCURS 1 TO 100 TIMES DEPENDING ON WS-COUNT.
      10 ITEM-DATA PIC X(10).
```

```java
private int wsCount;
private List<String> wsItem = new ArrayList<>();

// When reading, only process wsItem.subList(0, wsCount)
```

## Level 88 Condition Names

### Single Value

```cobol
01 WS-STATUS PIC X.
   88 VALID   VALUE 'V'.
   88 INVALID VALUE 'I'.
```

```java
public enum WsStatus {
    VALID('V'),
    INVALID('I');

    private final char code;
    WsStatus(char code) { this.code = code; }

    public static WsStatus fromCode(char c) {
        for (WsStatus s : values()) {
            if (s.code == c) return s;
        }
        return null;
    }
}
```

### Multiple Values

```cobol
01 WS-CHAR PIC X.
   88 IS-VOWEL VALUE 'A' 'E' 'I' 'O' 'U'.
   88 IS-DIGIT VALUE '0' THRU '9'.
```

```java
public boolean isVowel(char c) {
    return "AEIOU".indexOf(c) >= 0;
}

public boolean isDigit(char c) {
    return c >= '0' && c <= '9';
}
```

### Range Values

```cobol
01 WS-SCORE PIC 999.
   88 PASSING VALUE 60 THRU 100.
   88 FAILING VALUE 0 THRU 59.
```

```java
public boolean isPassing(int score) {
    return score >= 60 && score <= 100;
}

public boolean isFailing(int score) {
    return score >= 0 && score <= 59;
}
```

## REDEFINES Patterns

### Type Interpretation

```cobol
01 WS-DATE.
   05 WS-DATE-NUM  PIC 9(8).
   05 WS-DATE-PARTS REDEFINES WS-DATE-NUM.
      10 WS-YEAR  PIC 9(4).
      10 WS-MONTH PIC 9(2).
      10 WS-DAY   PIC 9(2).
```

```java
public class WsDate {
    private int dateNum;

    public int getDateNum() { return dateNum; }
    public void setDateNum(int d) { this.dateNum = d; }

    // REDEFINES accessors
    public int getYear() { return dateNum / 10000; }
    public int getMonth() { return (dateNum / 100) % 100; }
    public int getDay() { return dateNum % 100; }

    public void setYear(int y) {
        dateNum = y * 10000 + getMonth() * 100 + getDay();
    }
}
```

### Discriminated Union

```cobol
01 WS-RECORD.
   05 WS-TYPE PIC X.
   05 WS-DATA-A.
      10 FIELD-A1 PIC X(10).
      10 FIELD-A2 PIC 9(5).
   05 WS-DATA-B REDEFINES WS-DATA-A.
      10 FIELD-B1 PIC X(5).
      10 FIELD-B2 PIC X(5).
      10 FIELD-B3 PIC 9(5).
```

```java
public abstract class WsRecord {
    protected char wsType;

    public static WsRecord parse(byte[] data) {
        char type = (char) data[0];
        if (type == 'A') return new WsDataA(data);
        if (type == 'B') return new WsDataB(data);
        throw new IllegalArgumentException("Unknown type: " + type);
    }
}

public class WsDataA extends WsRecord {
    private String fieldA1;
    private int fieldA2;
}

public class WsDataB extends WsRecord {
    private String fieldB1;
    private String fieldB2;
    private int fieldB3;
}
```

## Sign Handling

COBOL signs can be stored differently:

| Sign Type | Storage | Java Handling |
|-----------|---------|---------------|
| `SIGN LEADING` | First byte | Parse sign from position 0 |
| `SIGN TRAILING` | Last byte | Parse sign from last position |
| `SIGN LEADING SEPARATE` | Separate byte | '-' or '+' prefix |
| `SIGN TRAILING SEPARATE` | Separate byte | '-' or '+' suffix |

```java
// COBOL: PIC S9(5) SIGN TRAILING SEPARATE
// Value: "12345-" means -12345

public int parseSignTrailingSeparate(String s) {
    String num = s.substring(0, s.length() - 1);
    char sign = s.charAt(s.length() - 1);
    int value = Integer.parseInt(num);
    return sign == '-' ? -value : value;
}
```

## File Status Codes

Common COBOL file status codes to handle in Java:

| Status | Meaning | Java Exception/Handling |
|--------|---------|------------------------|
| 00 | Success | Normal return |
| 10 | End of file | Return null or throw EOFException |
| 22 | Duplicate key | Throw DuplicateKeyException |
| 23 | Record not found | Return Optional.empty() |
| 30 | Permanent error | Throw IOException |
| 35 | File not found | Throw FileNotFoundException |
| 39 | File attribute conflict | Throw IllegalStateException |
| 41 | File already open | Check state before open |
| 42 | File not open | Check state before operation |
| 47 | READ on file not opened for input | Throw IllegalStateException |
