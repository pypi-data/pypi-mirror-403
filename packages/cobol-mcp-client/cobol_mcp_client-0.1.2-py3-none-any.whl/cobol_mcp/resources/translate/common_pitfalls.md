# Common COBOL to Java Translation Pitfalls

## The "JOBOL" Anti-Pattern

The most common mistake is producing "JOBOL"—Java code that preserves COBOL structure and semantics instead of being idiomatic Java.

### Signs of JOBOL

```java
// JOBOL: Retains COBOL naming and structure
public class WS_CUSTOMER_RECORD {
    public String WS_CUST_ID;
    public String WS_CUST_NAME;
    public BigDecimal WS_CUST_BALANCE;

    public void PERFORM_VALIDATE_CUSTOMER() {
        if (WS_CUST_ID == null) {
            MOVE_SPACES_TO_WS_MESSAGE();
        }
    }
}
```

### Proper Java

```java
// Correct: Idiomatic Java
public class Customer {
    private String id;
    private String name;
    private BigDecimal balance;

    public ValidationResult validate() {
        if (id == null || id.isBlank()) {
            return ValidationResult.invalid("Customer ID required");
        }
        return ValidationResult.valid();
    }
}
```

## Numeric Precision Errors

### Pitfall: Using double for Financial Calculations

```java
// WRONG: Precision loss
double balance = 100.00;
double tax = balance * 0.0825;  // 8.250000000000001

// COBOL: 05 WS-TAX PIC S9(5)V99 COMP-3.
// This is EXACT in COBOL, must be exact in Java
```

### Solution: Always Use BigDecimal

```java
// CORRECT: Exact precision
BigDecimal balance = new BigDecimal("100.00");
BigDecimal taxRate = new BigDecimal("0.0825");
BigDecimal tax = balance.multiply(taxRate)
    .setScale(2, RoundingMode.HALF_UP);  // 8.25
```

### COMP-3 Implicit Decimal

```cobol
05 WS-AMOUNT PIC S9(5)V99 COMP-3 VALUE 12345.67.
```

The `V` is an implied decimal—COBOL stores `1234567` but treats it as `12345.67`.

```java
// WRONG: Ignoring implied decimal
int wsAmount = 1234567;  // This loses the decimal semantics

// CORRECT: Respect the implied decimal
BigDecimal wsAmount = new BigDecimal("12345.67");
```

## Index Off-By-One Errors

### COBOL Arrays Are 1-Based

```cobol
01 WS-TABLE.
   05 WS-ITEM OCCURS 10 TIMES PIC X(5).

MOVE 'FIRST' TO WS-ITEM(1).
```

```java
// WRONG: Using COBOL index directly
String[] wsItem = new String[10];
wsItem[1] = "FIRST";  // This is the SECOND element!

// CORRECT: Convert to 0-based
wsItem[0] = "FIRST";

// Or encapsulate the conversion:
public void setItem(int cobolIndex, String value) {
    items[cobolIndex - 1] = value;
}
```

## String Handling Differences

### COBOL Strings Are Fixed-Width, Space-Padded

```cobol
05 WS-NAME PIC X(10) VALUE 'JOHN'.
* Storage: 'JOHN      ' (6 trailing spaces)
```

```java
// WRONG: Naive assignment
String wsName = "JOHN";  // No padding

// CORRECT for strict compatibility:
String wsName = String.format("%-10s", "JOHN");  // "JOHN      "

// Or use a wrapper class
public class CobolString {
    private final String value;
    private final int length;

    public CobolString(String value, int length) {
        this.length = length;
        this.value = pad(value);
    }

    private String pad(String s) {
        if (s.length() >= length) return s.substring(0, length);
        return String.format("%-" + length + "s", s);
    }
}
```

### MOVE Truncation Behavior

COBOL silently truncates on MOVE:

```cobol
05 WS-SHORT PIC X(5).
MOVE 'VERYLONGSTRING' TO WS-SHORT.
* Result: 'VERYL' (truncated, no error)
```

```java
// WRONG: Java throws exception or keeps full string
String wsShort = "VERYLONGSTRING";  // Full string kept

// CORRECT: Implement truncation
public void moveTo(String source, int maxLen) {
    return source.length() > maxLen
        ? source.substring(0, maxLen)
        : source;
}
```

## Control Flow Mistakes

### PERFORM THRU Misunderstanding

```cobol
PERFORM PARA-A THRU PARA-C.

PARA-A.
    DISPLAY 'A'.
PARA-B.
    DISPLAY 'B'.
PARA-C.
    DISPLAY 'C'.
```

This executes A, B, and C in sequence.

```java
// WRONG: Only calling one method
paraA();  // Missing B and C

// CORRECT: Include all paragraphs in range
public void paraAThroughC() {
    paraA();
    paraB();
    paraC();
}
```

### GO TO with ALTER

Some legacy COBOL uses `ALTER` to modify `GO TO` targets at runtime. This requires a state machine:

```java
// For complex GO TO patterns with ALTER
private Paragraph nextParagraph = Paragraph.INIT;

public void execute() {
    while (nextParagraph != Paragraph.EXIT) {
        switch (nextParagraph) {
            case INIT -> { /* code */ nextParagraph = Paragraph.PROCESS; }
            case PROCESS -> { /* code */ nextParagraph = Paragraph.EXIT; }
        }
    }
}
```

## Condition Name (88-Level) Misuse

### Pitfall: Checking Value Instead of Condition

```cobol
01 WS-STATUS PIC X.
   88 IS-ACTIVE VALUE 'A'.
   88 IS-INACTIVE VALUE 'I'.

IF IS-ACTIVE
    PERFORM ACTIVE-PROCESSING.
```

```java
// WRONG: Checking the wrong thing
if (wsStatus.equals("IS-ACTIVE")) {  // Comparing to literal "IS-ACTIVE"

// WRONG: Comparing to constant name as string
if ("ACTIVE".equals(wsStatus)) {  // COBOL value is 'A', not "ACTIVE"

// CORRECT: Check the actual value
if (wsStatus == 'A') {
    activeProcessing();
}

// BETTER: Use enum
if (status == Status.ACTIVE) {
    activeProcessing();
}
```

## File Status Ignored

COBOL programs check FILE STATUS after every file operation:

```cobol
READ CUSTOMER-FILE INTO WS-CUSTOMER.
IF WS-FILE-STATUS NOT = '00'
    PERFORM FILE-ERROR-HANDLER.
```

```java
// WRONG: Ignoring potential errors
String line = reader.readLine();
processLine(line);  // What if line is null?

// CORRECT: Handle all status conditions
public Optional<Customer> readNext() {
    try {
        String line = reader.readLine();
        if (line == null) {
            fileStatus = "10";  // EOF
            return Optional.empty();
        }
        fileStatus = "00";
        return Optional.of(parseCustomer(line));
    } catch (IOException e) {
        fileStatus = "30";  // Permanent error
        throw new FileAccessException(e);
    }
}
```

## SQL Translation Errors

### Host Variable Mapping

```cobol
EXEC SQL
    SELECT BALANCE INTO :WS-BALANCE
    FROM ACCOUNTS
    WHERE ACCT_ID = :WS-ACCT-ID
END-EXEC.
```

```java
// WRONG: Using string concatenation (SQL injection!)
String sql = "SELECT BALANCE FROM ACCOUNTS WHERE ACCT_ID = '" + acctId + "'";

// CORRECT: Use PreparedStatement parameters
String sql = "SELECT BALANCE FROM ACCOUNTS WHERE ACCT_ID = ?";
try (PreparedStatement ps = conn.prepareStatement(sql)) {
    ps.setString(1, acctId);
    ResultSet rs = ps.executeQuery();
    // ...
}
```

### SQLCODE Not Checked

```cobol
EXEC SQL SELECT ... END-EXEC.
IF SQLCODE = 100
    MOVE 'NOT FOUND' TO WS-MESSAGE.
```

```java
// WRONG: Assuming query always succeeds
Customer c = repo.findById(id).get();  // Throws if not found

// CORRECT: Handle all SQL conditions
Optional<Customer> result = repo.findById(id);
if (result.isEmpty()) {
    sqlcode = 100;
    message = "NOT FOUND";
    return;
}
sqlcode = 0;
customer = result.get();
```

## Sign Handling

### Signed vs Unsigned Confusion

```cobol
05 WS-AMOUNT PIC S9(5)V99.   * Signed
05 WS-COUNT  PIC 9(5).       * Unsigned
```

```java
// WRONG: Treating signed as unsigned
int wsAmount = Math.abs(value);  // Loses sign!

// CORRECT: Preserve sign semantics
int wsAmount = value;  // Can be negative

// For truly unsigned fields, validate:
if (wsCount < 0) {
    throw new IllegalArgumentException("Count cannot be negative");
}
```

## Copybook Duplication

### Pitfall: Inlining Copybook in Every Class

```cobol
COPY CUSTCOPY.  * Used in 50 programs
```

```java
// WRONG: Duplicating structure in each class
public class Program1 {
    private String custId;
    private String custName;
    // Same fields repeated in Program2, Program3...
}

// CORRECT: Single shared class
public class CustomerCopybook {
    private String custId;
    private String custName;
}

// Programs reference the shared class
public class Program1 {
    private CustomerCopybook customer;
}
```

## REDEFINES Data Corruption

### Pitfall: Independent Variables

```cobol
01 WS-DATA.
   05 WS-NUM  PIC 9(8).
   05 WS-DATE REDEFINES WS-NUM.
      10 WS-YEAR  PIC 9(4).
      10 WS-MONTH PIC 9(2).
      10 WS-DAY   PIC 9(2).
```

```java
// WRONG: Separate variables can become inconsistent
private int wsNum;
private int wsYear;
private int wsMonth;
private int wsDay;

// Setting wsNum doesn't update date parts!
wsNum = 20240115;
// wsYear is still 0, not 2024

// CORRECT: Computed properties from single source
private int wsNum;

public int getYear() { return wsNum / 10000; }
public int getMonth() { return (wsNum / 100) % 100; }
public int getDay() { return wsNum % 100; }

public void setDate(int year, int month, int day) {
    wsNum = year * 10000 + month * 100 + day;
}
```

## Performance Pitfalls

### Excessive Object Creation

```java
// WRONG: Creating objects in tight loops
for (int i = 0; i < 1000000; i++) {
    BigDecimal value = new BigDecimal(String.valueOf(amounts[i]));
    total = total.add(value);
}

// CORRECT: Reuse patterns, batch operations
BigDecimal[] values = Arrays.stream(amounts)
    .mapToObj(BigDecimal::valueOf)
    .toArray(BigDecimal[]::new);

BigDecimal total = Arrays.stream(values)
    .reduce(BigDecimal.ZERO, BigDecimal::add);
```

### String Concatenation in Loops

```java
// WRONG: String concatenation creates many objects
String output = "";
for (Customer c : customers) {
    output += c.toString() + "\n";
}

// CORRECT: Use StringBuilder
StringBuilder sb = new StringBuilder();
for (Customer c : customers) {
    sb.append(c).append("\n");
}
String output = sb.toString();
```

## Dead Code Not Removed

COBOL programs often have unreachable code. Remove it during migration:

```cobol
* This paragraph is never called
UNUSED-PARA.
    DISPLAY 'NEVER EXECUTED'.
```

```java
// WRONG: Translating dead code
public void unusedPara() {
    System.out.println("NEVER EXECUTED");
}

// CORRECT: Don't include dead code in translation
// (after verifying it's truly dead)
```

## Testing Gaps

### Pitfall: No Semantic Equivalence Testing

```java
// WRONG: Just compiling and deploying
// The Java code compiles, so it must be correct!

// CORRECT: Run parallel tests
public class TranslationTest {
    @Test
    void sameOutputAsCobol() {
        byte[] cobolInput = loadTestData("customer_input.dat");
        byte[] expectedOutput = loadExpectedOutput("cobol_output.dat");

        byte[] javaOutput = javaProgram.process(cobolInput);

        assertArrayEquals(expectedOutput, javaOutput);
    }
}
```

### No Edge Case Coverage

Test these COBOL-specific scenarios:
- Maximum field values (PIC 9(9) = 999999999)
- Minimum values (signed fields with negative max)
- Empty/space-filled strings
- Zero-padded numeric strings
- File status codes (00, 10, 22, 23, etc.)
- SQLCODE conditions (0, 100, -803, etc.)
