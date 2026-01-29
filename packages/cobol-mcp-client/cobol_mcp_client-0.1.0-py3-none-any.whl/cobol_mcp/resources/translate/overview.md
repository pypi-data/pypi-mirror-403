## Overview

Translate COBOL programs to clean, maintainable Java—not "JOBOL." Focus on preserving business logic while producing idiomatic object-oriented code that Java developers can understand and maintain.

## Translation Workflow

```
1. Analyze COBOL structure and dependencies
2. Map data divisions to Java classes
3. Transform procedure division to methods
4. Convert file handling and database access
5. Validate semantic equivalence
```

## COBOL Program Structure to Java Mapping

| COBOL Division | Java Equivalent |
|----------------|-----------------|
| IDENTIFICATION DIVISION | Class declaration, package, comments |
| ENVIRONMENT DIVISION | Configuration classes, resource paths |
| DATA DIVISION | Instance variables, DTOs, records |
| PROCEDURE DIVISION | Methods |

### Division-Level Translation

**IDENTIFICATION DIVISION** → Java class header:
```java
package com.company.legacy;

/**
 * Migrated from: PROGRAM-ID. CUSTMAINT
 * Original Author: [from AUTHOR clause]
 */
public class CustomerMaintenance {
```

**WORKING-STORAGE SECTION** → Instance variables and inner classes for group items.

**LINKAGE SECTION** → Method parameters or separate DTO classes.

**FILE SECTION** → File handling classes or database entities.

## Data Type Mappings

| COBOL Type | Java Equivalent | Notes |
|------------|-----------------|-------|
| `PIC X(n)` | `String` | Pad/truncate to n chars if strict |
| `PIC 9(n)` | `int` or `long` | Use `long` if n > 9 |
| `PIC 9(n)V9(m)` | `BigDecimal` | Required for financial precision |
| `PIC S9(n)` | `int` or `long` | Signed integer |
| `COMP` / `COMP-5` | `int` or `long` | Binary storage |
| `COMP-3` | `BigDecimal` | Packed decimal |
| `OCCURS n TIMES` | `Type[]` or `List<Type>` | Arrays |
| `88 level` | `enum` or boolean methods | See condition names section |

### Critical: Financial Calculations

Always use `BigDecimal` for monetary values. Never use `double` or `float`:

```java
// COBOL: 05 WS-AMOUNT PIC S9(7)V99 COMP-3.
private BigDecimal wsAmount = BigDecimal.ZERO;

// COBOL: ADD WS-TAX TO WS-AMOUNT.
wsAmount = wsAmount.add(wsTax);

// COBOL: MULTIPLY WS-RATE BY WS-AMOUNT GIVING WS-TOTAL.
BigDecimal wsTotal = wsAmount.multiply(wsRate);
```

## Group Items and Copybooks

### Group Items → Java Classes

```cobol
01 CUSTOMER-RECORD.
   05 CUST-ID        PIC 9(6).
   05 CUST-NAME      PIC X(30).
   05 CUST-ADDRESS.
      10 ADDR-LINE1  PIC X(30).
      10 ADDR-CITY   PIC X(20).
      10 ADDR-STATE  PIC XX.
      10 ADDR-ZIP    PIC 9(5).
```

Becomes:

```java
public class CustomerRecord {
    private int custId;
    private String custName;
    private CustomerAddress custAddress;

    public static class CustomerAddress {
        private String addrLine1;
        private String addrCity;
        private String addrState;
        private int addrZip;
        // getters/setters
    }
    // getters/setters
}
```

### REDEFINES → Union Pattern

For `REDEFINES`, create separate accessor methods or use a discriminator:

```java
public class EmployeeRecord {
    private char employeeType; // 'P' or 'T'
    private byte[] rawData;

    public PermanentEmployee asPermanent() {
        if (employeeType != 'P') throw new IllegalStateException();
        return new PermanentEmployee(rawData);
    }

    public TemporaryEmployee asTemporary() {
        if (employeeType != 'T') throw new IllegalStateException();
        return new TemporaryEmployee(rawData);
    }
}
```

### Copybooks → Shared Classes

Generate one Java class per copybook. Reference it across all programs that `COPY` it:

```java
// Generated from CUSTCOPY.cpy - DO NOT EDIT
public class CustCopy {
    // shared data structure
}
```

## 88-Level Condition Names

Translate to enums for mutually exclusive states:

```cobol
01 WS-STATUS PIC X.
   88 STATUS-ACTIVE     VALUE 'A'.
   88 STATUS-INACTIVE   VALUE 'I'.
   88 STATUS-PENDING    VALUE 'P'.
```

```java
public enum Status {
    ACTIVE('A'),
    INACTIVE('I'),
    PENDING('P');

    private final char code;
    Status(char code) { this.code = code; }
    public char getCode() { return code; }

    public static Status fromCode(char code) {
        for (Status s : values()) {
            if (s.code == code) return s;
        }
        throw new IllegalArgumentException("Unknown status: " + code);
    }
}
```

For boolean conditions within a field, use predicate methods:

```java
public boolean isValidAmount() {
    return amount.compareTo(BigDecimal.ZERO) > 0
        && amount.compareTo(MAX_AMOUNT) <= 0;
}
```

## Control Flow Translation

### PERFORM → Method Calls

```cobol
PERFORM VALIDATE-INPUT.
PERFORM CALCULATE-TOTALS THRU CALCULATE-EXIT.
PERFORM PROCESS-RECORD UNTIL END-OF-FILE.
PERFORM PROCESS-ITEM VARYING I FROM 1 BY 1 UNTIL I > 10.
```

```java
validateInput();
calculateTotals();  // THRU: include all logic in one method
while (!endOfFile) { processRecord(); }
for (int i = 1; i <= 10; i++) { processItem(i); }
```

### EVALUATE → Switch or If-Else

```cobol
EVALUATE TRUE
    WHEN AGE < 18
        MOVE 'MINOR' TO CATEGORY
    WHEN AGE < 65
        MOVE 'ADULT' TO CATEGORY
    WHEN OTHER
        MOVE 'SENIOR' TO CATEGORY
END-EVALUATE.
```

```java
// EVALUATE TRUE with conditions → if-else chain
if (age < 18) {
    category = "MINOR";
} else if (age < 65) {
    category = "ADULT";
} else {
    category = "SENIOR";
}
```

```cobol
EVALUATE WS-CODE
    WHEN 'A' PERFORM PROCESS-A
    WHEN 'B' THRU 'D' PERFORM PROCESS-BD
    WHEN OTHER PERFORM PROCESS-DEFAULT
END-EVALUATE.
```

```java
// Simple EVALUATE → switch (Java 17+)
switch (wsCode) {
    case 'A' -> processA();
    case 'B', 'C', 'D' -> processBD();  // THRU becomes multiple cases
    default -> processDefault();
}
```

### GO TO Elimination

Avoid translating `GO TO` directly. Restructure to use:
- Early returns
- Loop break/continue with labels
- State machine pattern for complex control flow

```java
// State machine for complex GO TO patterns
enum State { START, VALIDATE, PROCESS, ERROR, END }
State state = State.START;

while (state != State.END) {
    switch (state) {
        case START -> state = initialize() ? State.VALIDATE : State.ERROR;
        case VALIDATE -> state = validate() ? State.PROCESS : State.ERROR;
        case PROCESS -> { process(); state = State.END; }
        case ERROR -> { handleError(); state = State.END; }
    }
}
```

## String Operations

| COBOL | Java |
|-------|------|
| `STRING A B DELIMITED SIZE INTO C` | `c = a + b` or `StringBuilder` |
| `UNSTRING A DELIMITED BY ',' INTO B C D` | `String[] parts = a.split(",")` |
| `INSPECT A TALLYING CT FOR ALL 'X'` | `a.chars().filter(c -> c == 'X').count()` |
| `INSPECT A REPLACING ALL 'X' BY 'Y'` | `a.replace("X", "Y")` |

### MOVE CORRESPONDING

Use a mapper or explicit field-by-field copy:

```java
// Manual mapping (preferred for clarity)
target.setField1(source.getField1());
target.setField2(source.getField2());

// Or use MapStruct/ModelMapper for complex cases
```

## File Handling

### Sequential Files

```cobol
SELECT CUSTOMER-FILE ASSIGN TO 'CUSTFILE'
    ORGANIZATION IS SEQUENTIAL
    FILE STATUS IS WS-FILE-STATUS.
```

```java
public class CustomerFileReader implements AutoCloseable {
    private BufferedReader reader;
    private String fileStatus = "00";

    public void open(String path) throws IOException {
        reader = new BufferedReader(new FileReader(path));
        fileStatus = "00";
    }

    public CustomerRecord read() throws IOException {
        String line = reader.readLine();
        if (line == null) {
            fileStatus = "10"; // EOF
            return null;
        }
        return parseRecord(line);
    }

    public String getFileStatus() { return fileStatus; }

    @Override
    public void close() throws IOException {
        if (reader != null) reader.close();
    }
}
```

### Indexed Files (KSDS) → Database or Map

For VSAM KSDS files, migrate to:
- **Database table** with primary key (recommended)
- **TreeMap** for in-memory with key access
- **H2/SQLite** for embedded database

```java
// KSDS-style access via JPA
@Entity
@Table(name = "CUSTOMER")
public class Customer {
    @Id
    private String customerId;  // Primary key = KSDS key
    // fields...
}

// Repository
public interface CustomerRepository extends JpaRepository<Customer, String> {
    // READ with key: findById()
    // READ sequential: findAll(Sort.by("customerId"))
}
```

## Embedded SQL (DB2)

### Host Variables → PreparedStatement Parameters

```cobol
EXEC SQL
    SELECT CUST_NAME, CUST_BALANCE
    INTO :WS-CUST-NAME, :WS-CUST-BALANCE
    FROM CUSTOMER
    WHERE CUST_ID = :WS-CUST-ID
END-EXEC.
```

```java
String sql = "SELECT CUST_NAME, CUST_BALANCE FROM CUSTOMER WHERE CUST_ID = ?";
try (PreparedStatement ps = connection.prepareStatement(sql)) {
    ps.setString(1, wsCustId);
    try (ResultSet rs = ps.executeQuery()) {
        if (rs.next()) {
            wsCustName = rs.getString("CUST_NAME");
            wsCustBalance = rs.getBigDecimal("CUST_BALANCE");
            sqlcode = 0;
        } else {
            sqlcode = 100; // NOT FOUND
        }
    }
} catch (SQLException e) {
    sqlcode = e.getErrorCode();
}
```

### SQLCODE Handling

```java
public class SqlResult {
    public static final int SUCCESS = 0;
    public static final int NOT_FOUND = 100;
    public static final int DUPLICATE = -803;

    private int sqlcode;
    // getters/setters
}
```

## CICS Transaction Migration

### EXEC CICS → Spring/Java EE

| CICS Command | Java Equivalent |
|--------------|-----------------|
| `EXEC CICS LINK PROGRAM(...)` | Method call or REST client |
| `EXEC CICS XCTL PROGRAM(...)` | Forward/redirect |
| `EXEC CICS RETURN` | `return` statement |
| `EXEC CICS READ FILE(...)` | JPA/JDBC query |
| `EXEC CICS SEND MAP(...)` | View/template rendering |
| `EXEC CICS RECEIVE MAP(...)` | Form binding |

For CICS-to-Spring migration, map transactions to REST endpoints or Spring Batch jobs.

## JCL/Batch → Spring Batch

```
//STEP1    EXEC PGM=CUSTPROC
//INPUT    DD DSN=PROD.CUSTOMER.FILE
//OUTPUT   DD DSN=PROD.CUSTOMER.REPORT
```

```java
@Configuration
public class CustomerBatchConfig {

    @Bean
    public Job customerProcessJob(JobRepository jobRepository,
                                   Step processStep) {
        return new JobBuilder("customerProcessJob", jobRepository)
            .start(processStep)
            .build();
    }

    @Bean
    public Step processStep(JobRepository jobRepository,
                            PlatformTransactionManager txManager,
                            ItemReader<Customer> reader,
                            ItemProcessor<Customer, Report> processor,
                            ItemWriter<Report> writer) {
        return new StepBuilder("processStep", jobRepository)
            .<Customer, Report>chunk(100, txManager)
            .reader(reader)
            .processor(processor)
            .writer(writer)
            .build();
    }
}
```

## Avoiding "JOBOL"

**DO NOT** produce code like this:

```java
// BAD: JOBOL - COBOL semantics in Java syntax
public class WS_CUSTOMER_RECORD {
    public String WS_CUST_ID;      // PIC X(6)
    public String WS_CUST_NAME;    // PIC X(30)
    public void PERFORM_VALIDATE() { ... }
    public void PERFORM_PROCESS() { ... }
}
```

**DO** produce idiomatic Java:

```java
// GOOD: Proper Java
public class Customer {
    private String id;
    private String name;

    public void validate() { ... }
    public void process() { ... }
}
```

Key principles:
1. Use camelCase naming
2. Create proper class hierarchies
3. Encapsulate data with getters/setters
4. Extract reusable logic into utilities
5. Remove dead code during migration
6. Use modern Java features (records, streams, optionals)

## Validation Checklist

Before considering translation complete:

- [ ] All data types mapped correctly (especially decimals)
- [ ] Business logic preserved (compare outputs)
- [ ] File operations handle all status codes
- [ ] SQL error handling matches SQLCODE checks
- [ ] No COBOL naming conventions in Java code
- [ ] Unit tests cover critical business rules
- [ ] Performance tested for batch operations
