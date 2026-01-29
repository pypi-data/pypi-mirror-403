# CICS to Spring/Java EE Migration Patterns

## CICS Command Quick Reference

| CICS Command | Purpose | Java/Spring Equivalent |
|--------------|---------|----------------------|
| `LINK` | Call another program, return | Method call, `@Service` injection |
| `XCTL` | Transfer control, no return | Forward, redirect, return new view |
| `RETURN` | End program | `return` statement |
| `ABEND` | Abnormal end | `throw new RuntimeException()` |
| `READ` | Read file/record | JPA `findById()`, JDBC query |
| `WRITE` | Write new record | JPA `save()`, JDBC insert |
| `REWRITE` | Update record | JPA `save()`, JDBC update |
| `DELETE` | Delete record | JPA `delete()`, JDBC delete |
| `SEND MAP` | Display screen | Return view/template |
| `RECEIVE MAP` | Get user input | `@RequestParam`, form binding |
| `SEND TEXT` | Output text | Response body |
| `START` | Schedule transaction | `@Scheduled`, message queue |
| `RETRIEVE` | Get started data | Method parameter, queue message |
| `SYNCPOINT` | Commit | `@Transactional` commit |
| `SYNCPOINT ROLLBACK` | Rollback | `@Transactional` rollback |

## Program Control

### EXEC CICS LINK → Method Call

```cobol
EXEC CICS LINK
    PROGRAM('CUSTINQ')
    COMMAREA(WS-COMMAREA)
    LENGTH(WS-COMM-LEN)
END-EXEC.
```

```java
@Service
public class MainService {
    @Autowired
    private CustomerInquiryService custInqService;

    public void process(CommArea commArea) {
        // LINK → direct service call
        custInqService.inquire(commArea);
        // Execution continues here after call returns
    }
}
```

### EXEC CICS XCTL → Controller Forward

```cobol
EXEC CICS XCTL
    PROGRAM('ORDPROC')
    COMMAREA(WS-COMMAREA)
END-EXEC.
```

```java
@Controller
public class MainController {

    @PostMapping("/transfer")
    public String transfer(@ModelAttribute CommArea commArea,
                          RedirectAttributes attrs) {
        attrs.addFlashAttribute("commArea", commArea);
        // XCTL → redirect (control does not return)
        return "redirect:/order/process";
    }
}
```

### EXEC CICS RETURN

```cobol
EXEC CICS RETURN
    TRANSID('MNU1')
    COMMAREA(WS-COMMAREA)
END-EXEC.
```

```java
@Controller
public class OrderController {

    @PostMapping("/complete")
    public String complete(@ModelAttribute CommArea commArea,
                          HttpSession session) {
        session.setAttribute("commArea", commArea);
        // RETURN TRANSID → redirect to next transaction
        return "redirect:/menu";
    }
}
```

## File/Data Access

### EXEC CICS READ → JPA/JDBC

```cobol
EXEC CICS READ
    FILE('CUSTFILE')
    INTO(WS-CUSTOMER)
    RIDFLD(WS-CUST-ID)
    KEYLENGTH(6)
    RESP(WS-RESP)
END-EXEC.

IF WS-RESP = DFHRESP(NOTFND)
    PERFORM NOT-FOUND-HANDLER
END-IF.
```

```java
@Repository
public interface CustomerRepository extends JpaRepository<Customer, String> {
}

@Service
public class CustomerService {
    @Autowired
    private CustomerRepository repo;

    public Optional<Customer> read(String custId) {
        // READ FILE → JPA findById
        return repo.findById(custId);
    }
}

// Usage:
customerService.read(custId)
    .ifPresentOrElse(
        customer -> processCustomer(customer),
        () -> handleNotFound()  // DFHRESP(NOTFND)
    );
```

### EXEC CICS WRITE → JPA Save (Insert)

```cobol
EXEC CICS WRITE
    FILE('CUSTFILE')
    FROM(WS-CUSTOMER)
    RIDFLD(WS-CUST-ID)
    KEYLENGTH(6)
    RESP(WS-RESP)
END-EXEC.

IF WS-RESP = DFHRESP(DUPREC)
    PERFORM DUPLICATE-HANDLER
END-IF.
```

```java
@Service
public class CustomerService {

    @Transactional
    public void write(Customer customer) {
        if (repo.existsById(customer.getId())) {
            throw new DuplicateKeyException("Customer exists");
        }
        repo.save(customer);
    }
}
```

### EXEC CICS REWRITE → JPA Save (Update)

```cobol
EXEC CICS READ
    FILE('CUSTFILE')
    INTO(WS-CUSTOMER)
    RIDFLD(WS-CUST-ID)
    UPDATE
END-EXEC.

MOVE 'UPDATED' TO CUST-STATUS.

EXEC CICS REWRITE
    FILE('CUSTFILE')
    FROM(WS-CUSTOMER)
END-EXEC.
```

```java
@Service
public class CustomerService {

    @Transactional
    public void update(String custId, Consumer<Customer> modifier) {
        Customer customer = repo.findById(custId)
            .orElseThrow(() -> new RecordNotFoundException(custId));
        modifier.accept(customer);  // Apply changes
        repo.save(customer);  // REWRITE
    }
}

// Usage:
customerService.update(custId, c -> c.setStatus("UPDATED"));
```

### EXEC CICS DELETE

```cobol
EXEC CICS DELETE
    FILE('CUSTFILE')
    RIDFLD(WS-CUST-ID)
    KEYLENGTH(6)
END-EXEC.
```

```java
@Service
public class CustomerService {

    @Transactional
    public void delete(String custId) {
        repo.deleteById(custId);
    }
}
```

### EXEC CICS STARTBR/READNEXT/ENDBR → Stream/Cursor

```cobol
EXEC CICS STARTBR
    FILE('CUSTFILE')
    RIDFLD(WS-START-KEY)
END-EXEC.

PERFORM UNTIL WS-EOF
    EXEC CICS READNEXT
        FILE('CUSTFILE')
        INTO(WS-CUSTOMER)
        RIDFLD(WS-CUST-ID)
        RESP(WS-RESP)
    END-EXEC

    IF WS-RESP = DFHRESP(ENDFILE)
        SET WS-EOF TO TRUE
    ELSE
        PERFORM PROCESS-CUSTOMER
    END-IF
END-PERFORM.

EXEC CICS ENDBR FILE('CUSTFILE') END-EXEC.
```

```java
@Service
public class CustomerService {

    public void browseAndProcess(String startKey) {
        // STARTBR/READNEXT/ENDBR → Stream with pagination
        try (Stream<Customer> stream = repo.streamByIdGreaterThanEqual(startKey)) {
            stream.forEach(this::processCustomer);
        }
    }

    // Or with explicit pagination:
    public void browseWithPaging(String startKey, int pageSize) {
        Pageable pageable = PageRequest.of(0, pageSize, Sort.by("id"));
        Page<Customer> page;

        do {
            page = repo.findByIdGreaterThanEqual(startKey, pageable);
            page.forEach(this::processCustomer);
            pageable = page.nextPageable();
        } while (page.hasNext());
    }
}
```

## Screen Handling (BMS)

### EXEC CICS SEND MAP → Thymeleaf/JSP View

```cobol
MOVE WS-CUST-ID   TO CUSTIDO.
MOVE WS-CUST-NAME TO CUSTNAMEO.
MOVE WS-BALANCE   TO BALANCEO.

EXEC CICS SEND
    MAP('CUSTMAP')
    MAPSET('CUSTSET')
    ERASE
END-EXEC.
```

```java
@Controller
public class CustomerController {

    @GetMapping("/customer/{id}")
    public String showCustomer(@PathVariable String id, Model model) {
        Customer customer = customerService.findById(id);

        // Map fields to view model (like BMS map)
        model.addAttribute("custId", customer.getId());
        model.addAttribute("custName", customer.getName());
        model.addAttribute("balance", customer.getBalance());

        return "customer/view";  // SEND MAP
    }
}
```

### EXEC CICS RECEIVE MAP → Form Binding

```cobol
EXEC CICS RECEIVE
    MAP('CUSTMAP')
    MAPSET('CUSTSET')
    INTO(CUSTMAPI)
END-EXEC.

MOVE CUSTIDI TO WS-CUST-ID.
MOVE CUSTNAMEI TO WS-CUST-NAME.
```

```java
@Controller
public class CustomerController {

    @PostMapping("/customer/update")
    public String updateCustomer(@ModelAttribute CustomerForm form) {
        // RECEIVE MAP → Spring form binding
        String custId = form.getCustId();
        String custName = form.getCustName();

        customerService.update(custId, custName);
        return "redirect:/customer/" + custId;
    }
}

public class CustomerForm {
    private String custId;
    private String custName;
    private BigDecimal balance;
    // getters/setters
}
```

## Transaction Control

### SYNCPOINT → @Transactional

```cobol
PERFORM UPDATE-CUSTOMER.
PERFORM UPDATE-ORDERS.

EXEC CICS SYNCPOINT END-EXEC.
```

```java
@Service
public class OrderService {

    @Transactional  // Commits at method end
    public void processOrder(Order order) {
        updateCustomer(order.getCustomerId());
        updateOrders(order);
        // SYNCPOINT happens automatically on successful return
    }
}
```

### SYNCPOINT ROLLBACK → Exception/Rollback

```cobol
IF WS-ERROR
    EXEC CICS SYNCPOINT ROLLBACK END-EXEC
END-IF.
```

```java
@Service
public class OrderService {

    @Transactional
    public void processOrder(Order order) {
        try {
            updateCustomer(order.getCustomerId());
            updateOrders(order);
        } catch (BusinessException e) {
            // SYNCPOINT ROLLBACK
            throw e;  // @Transactional will rollback
        }
    }
}
```

## Temporary Storage (TS Queue) → Cache/Session

### WRITEQ TS → Session/Cache

```cobol
EXEC CICS WRITEQ TS
    QUEUE(WS-QUEUE-NAME)
    FROM(WS-DATA)
    LENGTH(WS-DATA-LEN)
    ITEM(WS-ITEM-NUM)
END-EXEC.
```

```java
@Service
public class TempStorageService {
    @Autowired
    private CacheManager cacheManager;

    public int write(String queueName, Object data) {
        Cache cache = cacheManager.getCache("tsQueue");
        List<Object> items = getOrCreateQueue(cache, queueName);
        items.add(data);
        cache.put(queueName, items);
        return items.size();  // Item number
    }
}
```

### READQ TS → Cache/Session Read

```cobol
EXEC CICS READQ TS
    QUEUE(WS-QUEUE-NAME)
    INTO(WS-DATA)
    LENGTH(WS-DATA-LEN)
    ITEM(WS-ITEM-NUM)
END-EXEC.
```

```java
public Object read(String queueName, int itemNum) {
    Cache cache = cacheManager.getCache("tsQueue");
    List<Object> items = cache.get(queueName, List.class);
    if (items == null || itemNum > items.size()) {
        throw new QueueItemNotFoundException();
    }
    return items.get(itemNum - 1);  // CICS is 1-based
}
```

## Transient Data (TD Queue) → JMS/Message Queue

### WRITEQ TD → JMS Send

```cobol
EXEC CICS WRITEQ TD
    QUEUE('AUDITLOG')
    FROM(WS-AUDIT-REC)
    LENGTH(WS-AUDIT-LEN)
END-EXEC.
```

```java
@Service
public class AuditService {
    @Autowired
    private JmsTemplate jmsTemplate;

    public void writeAudit(AuditRecord record) {
        jmsTemplate.convertAndSend("auditLog", record);
    }
}
```

### READQ TD → JMS Listener

```cobol
EXEC CICS READQ TD
    QUEUE('AUDITLOG')
    INTO(WS-AUDIT-REC)
    LENGTH(WS-AUDIT-LEN)
END-EXEC.
```

```java
@Component
public class AuditProcessor {

    @JmsListener(destination = "auditLog")
    public void processAudit(AuditRecord record) {
        // Process the TD queue item
        auditRepository.save(record);
    }
}
```

## Error Handling

### HANDLE CONDITION → Exception Handling

```cobol
EXEC CICS HANDLE CONDITION
    NOTFND(NOT-FOUND-PARA)
    DUPREC(DUP-PARA)
    ERROR(ERROR-PARA)
END-EXEC.
```

```java
@ControllerAdvice
public class CicsExceptionHandler {

    @ExceptionHandler(RecordNotFoundException.class)
    public String handleNotFound(Model model) {
        model.addAttribute("message", "Record not found");
        return "error/notfound";  // NOT-FOUND-PARA equivalent
    }

    @ExceptionHandler(DuplicateKeyException.class)
    public String handleDuplicate(Model model) {
        model.addAttribute("message", "Duplicate record");
        return "error/duplicate";  // DUP-PARA equivalent
    }

    @ExceptionHandler(Exception.class)
    public String handleError(Exception e, Model model) {
        model.addAttribute("message", e.getMessage());
        return "error/general";  // ERROR-PARA equivalent
    }
}
```

### RESP/RESP2 Checking

```cobol
EXEC CICS READ ...
    RESP(WS-RESP)
    RESP2(WS-RESP2)
END-EXEC.

EVALUATE WS-RESP
    WHEN DFHRESP(NORMAL)    CONTINUE
    WHEN DFHRESP(NOTFND)    PERFORM NOT-FOUND
    WHEN DFHRESP(DISABLED)  PERFORM FILE-DISABLED
    WHEN OTHER              PERFORM UNEXPECTED-ERROR
END-EVALUATE.
```

```java
public class CicsResponse {
    public enum RespCode {
        NORMAL(0),
        NOTFND(13),
        DUPREC(14),
        DISABLED(84),
        INVREQ(16);

        private final int code;
        RespCode(int code) { this.code = code; }
    }
}

// In service method:
try {
    Customer c = repo.findById(id).orElseThrow(
        () -> new CicsException(RespCode.NOTFND));
} catch (DataAccessException e) {
    throw new CicsException(RespCode.DISABLED);
}
```

## COMMAREA → DTO Pattern

```cobol
01 WS-COMMAREA.
   05 CA-ACTION       PIC X.
   05 CA-CUST-ID      PIC X(6).
   05 CA-CUST-NAME    PIC X(30).
   05 CA-RETURN-CODE  PIC 9(2).
   05 CA-MESSAGE      PIC X(50).
```

```java
public class CommArea implements Serializable {
    private char action;
    private String custId;
    private String custName;
    private int returnCode;
    private String message;

    // COBOL MOVE equivalents
    public void setSuccess() {
        this.returnCode = 0;
        this.message = "";
    }

    public void setError(String msg) {
        this.returnCode = 99;
        this.message = msg;
    }

    // getters/setters
}
```

## START/RETRIEVE → Async Processing

### EXEC CICS START → @Async or Message Queue

```cobol
EXEC CICS START
    TRANSID('RPRT')
    FROM(WS-REPORT-PARMS)
    LENGTH(WS-PARM-LEN)
    INTERVAL(003000)
END-EXEC.
```

```java
@Service
public class ReportService {
    @Autowired
    private TaskScheduler scheduler;

    public void scheduleReport(ReportParams params) {
        // START with INTERVAL → scheduled task
        Instant startTime = Instant.now().plus(Duration.ofMinutes(30));
        scheduler.schedule(
            () -> generateReport(params),
            startTime
        );
    }

    @Async
    public CompletableFuture<Report> generateReportAsync(ReportParams params) {
        // START without INTERVAL → immediate async
        return CompletableFuture.completedFuture(generateReport(params));
    }
}
```

### EXEC CICS RETRIEVE → Read Scheduled Data

```cobol
EXEC CICS RETRIEVE
    INTO(WS-REPORT-PARMS)
    LENGTH(WS-PARM-LEN)
END-EXEC.
```

```java
// Parameters passed directly to the scheduled method
public void generateReport(ReportParams params) {
    // params contains the "retrieved" data
    String reportType = params.getReportType();
    LocalDate startDate = params.getStartDate();
    // ... generate report
}
```
