# IncludeCPP Changelog

## v4.9.7 (2026-01-29)

### CSSL MessageBox Fixes (`cssl-gui.MessageBox`)

- **Blocking `show()` by default**: `msg.show()` now blocks until the user clicks a button. Use `msg.show(wait=false)` for non-blocking behavior
- **`fmt::` color support in buttons**: Button text with ANSI color codes (e.g., `fmt::green("Accept")`) now renders with the correct foreground color
- **Standalone window**: MessageBox now uses a standalone `tk.Tk()` window instead of hidden root + Toplevel, fixing the instant-disappear bug
- **Null-safe event loop**: Fixed `NoneType` error when button click destroys window during `update()` call
- **`tk.Button` for color support**: Switched from `ttk.Button` to `tk.Button` to enable `fg` color parameter

### CLI

- **REPL prompt**: Changed from `cpp>` to `cssl>` to match the language name

---

## v4.9.6 (2026-01-28)

### CSSL GUI Framework (`cssl-gui`)

Native GUI framework built into CSSL with tkinter backend.

#### Widgets
- **`CsslWidget`**: Main window container with title, size, background color
  ```cssl
  include("cssl-gui");

  widget = CsslWidget("My App", 800, 600, "#1a1a2e");
  widget.show();
  widget.mainloop();
  ```

- **`CsslLabel`**: Text/image display with positioning
  ```cssl
  label = CsslLabel(widget, "Hello World", CsslGui::BigTitle);
  label.setPosition(CsslGui::Center);
  label.setColor("#ffffff");
  ```

- **`CsslButton`**: Clickable buttons with event handling
  ```cssl
  btn = CsslButton(widget, "Click Me", CsslGui::SmallTitle);
  btn.onClick(<<== {
      printl("Button clicked!");
  });
  ```

- **`CsslPicture`**: Image display with scaling
  ```cssl
  pic = CsslPicture(widget, "image.png", 200, 200);
  pic.setPosition(CsslGui::TopLeft);
  ```

- **`CsslSound`**: Audio playback (pygame backend)
  ```cssl
  sound = CsslSound("music.mp3");
  sound.play();
  sound.setVolume(0.5);
  ```

- **`CsslToolbar`**: Horizontal button toolbar
  ```cssl
  toolbar = CsslToolbar(widget);
  toolbar.addButton("Save", <<== { save(); });
  toolbar.addButton("Load", <<== { load(); });
  ```

- **`CsslInputField`**: Text input with filters
  ```cssl
  input = CsslInputField(widget, "Enter name...", CsslGui::SmallTitle);
  input.setFilter(CsslInputField::Alphabets);
  input.onChange(<<== { validate(); });
  ```

#### Position Constants
- `CsslGui::BigTitle`, `CsslGui::MediumTitle`, `CsslGui::SmallTitle` - Font sizes
- `CsslGui::Center`, `CsslGui::TopLeft`, `CsslGui::TopRight`, `CsslGui::BottomLeft`, `CsslGui::BottomRight` - Positioning

#### Input Filters
- `CsslInputField::All`, `CsslInputField::Alphabets`, `CsslInputField::Numbers`, `CsslInputField::Alphanumeric`

### CSSL Keyboard Framework (`cssl-keyboard`)

Cross-platform keyboard handling with pynput backend.

#### Features
- **Global key listening**: Monitor keyboard events system-wide
  ```cssl
  include("cssl-keyboard");

  keyboard = CsslKeyboardController();
  keyboard.listen(<<== key {
      printl("Key pressed: " + key);
  });
  ```

- **Hotkey registration**: Register global hotkeys
  ```cssl
  keyboard.hotkey("ctrl+s", <<== {
      printl("Save triggered!");
  });
  ```

- **Key state checking**: Check if specific keys are pressed
  ```cssl
  if (keyboard.isPressed("shift")) {
      printl("Shift is held down");
  }

  state = keyboard.getState("ctrl");
  ```

- **Controller methods**: `start()`, `stop()`, `isListening()`, `clearHotkeys()`

### Event System

#### CodeInfusion Event Handler (`<<==`)
- GUI and keyboard events support CSSL's `<<==` operator for inline code blocks
- Events receive context variables automatically (e.g., `key` for keyboard events)

---

## v4.9.5 (2026-01-27)

### Variable Modifiers

#### `local`, `static`, `freezed` Keywords
- **`local`**: Forbids global reference access (`@var` returns null), allows snapshots (`%var`)
  ```cssl
  local int privateCounter = 0;
  @privateCounter;  // Returns null (cannot access via @)
  snapshot(privateCounter);
  %privateCounter;  // Works normally
  ```

- **`static`**: Allows global reference access (`@var`), forbids snapshots (`%var` returns null)
  ```cssl
  static int cachedValue = 42;
  @cachedValue;     // Works normally
  %cachedValue;     // Returns null (cannot snapshot)
  ```

- **`local static`**: Forbids both `@` and `%` access
  ```cssl
  local static int internalOnly = 100;
  @internalOnly;    // Returns null
  %internalOnly;    // Returns null
  ```

- **`freezed`**: Creates immutable variables (reassignment returns null)
  ```cssl
  freezed string constant = "immutable";
  constant = "new value";  // Returns null (no change made)
  ```

### Function Modifier Fixes

#### `undefined` and `super` Error Handling
- **Per-statement error handling**: `undefined` and `super` modifiers now catch errors on each statement and continue execution
  ```cssl
  undefined define SafeFunc() {
      d = ?nonexistent;  // Error swallowed, continues
      x = 2;             // Executes
      return x;          // Returns 2
  }
  ```

### Generator Enhancements

#### send() Support with Yield Expressions
- **`received = yield value`**: Capture sent values in generators
  ```cssl
  generator<int> define Counter() {
      int value = 0;
      while (true) {
          received = yield value;
          if (received != null) {
              value = received;
          } else {
              value = value + 1;
          }
      }
  }

  counter = Counter();
  printl(counter.next());   // 0
  printl(counter.next());   // 1
  counter.send(100);        // Resume with value 100
  printl(counter.next());   // 101
  ```

- **`take(n)`**: Safely get first n values from any generator (including infinite)
- **`skip(n)`**: Skip n values and continue iteration
- **`send(value)`**: Send a value into the generator, becomes result of yield expression

### Bug Fixes
- Fixed generator scope management for proper variable updates in while loops
- Fixed `yield_expr` detection for generator function identification

---

## v4.9.3 (2026-01-27)

### New Features - Full Async/Await System

#### Async Functions
- **`async` function modifier**: Define async functions that return Futures
  ```cssl
  async define fetchData(string url) {
      result = http.get(url);
      return result;
  }

  // Calling returns Future immediately
  future f = fetchData("http://example.com");
  data = await f;
  ```

#### Await Keyword
- **`await`**: Wait for async operations to complete
  ```cssl
  data = await asyncFunction();
  result = await future;
  ```

#### Generator Functions with Yield
- **`yield` statement**: Create lazy iterators
  ```cssl
  generator<int> define Range(int n) {
      int i = 0;
      while (i < n) {
          yield i;
          i = i + 1;
      }
  }

  gen = Range(5);
  while (gen.has_next()) {
      printl(gen.next());  // 0, 1, 2, 3, 4
  }
  ```

#### Async Module (`async::` / `Async::`)
- **`async.run(func, *args)`**: Run function asynchronously, returns Future
- **`async.stop(future)`**: Cancel async operation
- **`async.wait(future, timeout?)`**: Wait for Future with optional timeout
- **`async.all(futures, timeout?)`**: Wait for all Futures to complete
- **`async.race(futures, timeout?)`**: Return first completed Future's result
- **`async.sleep(ms)`**: Async sleep for milliseconds

#### New Types
- **`CSSLFuture`**: Represents result of async operation
  - States: `pending`, `running`, `completed`, `cancelled`, `failed`
  - Methods: `result()`, `is_done()`, `cancel()`, `then(callback)`
- **`CSSLGenerator`**: Lazy iteration via yield
  - Methods: `next()`, `has_next()`, `send(val)`, `to_list()`, `take(n)`, `skip(n)`
- **`CSSLAsyncFunction`**: Wrapper for async-defined functions

### Parser Enhancements
- Added `async`, `yield`, `generator`, `future` keywords
- Added `async` to function modifiers
- Added `generator` and `future` to generic type keywords

### Type Stubs
- Updated `cssl_builtins.pyi` with full async type documentation
- Added `CSSLFuture`, `CSSLGenerator`, `AsyncModule` stubs

### Documentation
- Added comprehensive Async/Await section to CSSL documentation
- Added generator function examples and patterns

---

## v4.9.2 (2026-01-26)

### New Features - Builtin Function Hooks & Introspection

#### Builtin Function Hooks (`&builtin ++`)
- **Hook into any builtin function** with append mode:
  ```cssl
  embedded define __hook_print(msg) &printl ++ {
      printl("LOG: " + _result);  // _result has original's return value
  }

  // Now all printl calls trigger the hook AFTER original runs
  printl("Hello");  // Prints: "Hello" then "LOG: null"
  ```

- **Append mode semantics**: Original runs first, then hook body executes
- **`_result` variable**: Automatically contains the original function's return value
- **`local::` references**: Access hook context variables
  ```cssl
  local::_result   // Original's return value
  local::0         // First positional argument
  local::_args     // All positional arguments
  local::_kwargs   // All keyword arguments
  ```

#### New Builtins
- **`destroy(target)`**: Destroy object and free memory
  ```cssl
  list data = [1, 2, 3];
  destroy(data);  // Clears the list
  ```

- **`execute(code, context?)`**: Execute CSSL code string inline
  ```cssl
  result = execute("return 5 + 3;");  // Returns 8
  execute("printl(name);", {"name": "World"});  // With context
  ```

#### Parser Enhancements
- **Position syntax for hooks**: `&name[-1]` (places hook at specific position)
- **`local::varname`** token type for accessing hooked function locals

### Bug Fixes
- Fixed infinite recursion when hook body calls the hooked builtin
- Fixed `skip` keyword argument error in builtin hooks
- Fixed hook execution order (original now runs before hook body in append mode)

### Syntax Highlighting
- Added `local::` reference highlighting
- Added `_result`, `_args`, `_kwargs` special variable highlighting
- Added `destroy` and `execute` builtin highlighting

---

## v4.9.0 (2026-01-25)

### New Features - CSSL Language Enhancements

#### Binary Data Types
- **`bit`**: Single binary value (0 or 1)
  ```cssl
  bit flag = 1;
  flag.switch();    // Toggle: 1 -> 0
  flag.set(1);      // Set to 1
  flag.clear();     // Set to 0
  bit copy = flag.copy();
  ```

- **`byte`**: 8-bit value with `x^y` notation
  ```cssl
  byte b = 1^200;           // base^weight notation
  printl(b.value());        // 200
  printl(b.to_str());       // "11001000" (binary)
  b.switch(7);              // Toggle bit 7
  b.set(0, 1);              // Set bit 0 to 1
  printl(b.info());         // Full info dict
  byte r = b.reverse();     // Reverse bit order
  ```

- **`address`**: Memory reference (pointer-like)
  ```cssl
  string text = "Hello";
  address addr = address(text);  // Get address
  obj = addr.reflect();          // Dereference
  obj = reflect(addr);           // Also works

  // Use in functions
  define useAddress() {
      string val = reflect(addr);  // Access from anywhere
  }
  ```

#### Pointer Syntax (`?`)
- **`?name = obj`**: Create pointer to object (simple C-like syntax)
- **`?name`**: Dereference pointer to get object
  ```cssl
  string text = "Hello";
  ?ptr = text;                   // Create pointer

  define usePointer() {
      string val = ?ptr;         // Dereference: "Hello"
      printl(val);
  }
  usePointer();
  ```

#### Memory Functions
- **`address(obj)`**: Shortcut for `memory(obj).get("address")`
- **`reflect(addr)`**: Dereference an address to get the original object
- **`memory()`**: Now registers objects for later reflection

#### Snapshot Assignment
- **`%var = value`**: Direct snapshot assignment syntax
  ```cssl
  string greeting = "Hello";
  %savedGreeting = greeting;
  greeting = "Changed";
  printl(%savedGreeting);  // "Hello"
  ```

### Bug Fixes
- Fixed bit/byte method calls returning null in CSSL runtime
- Fixed parser not recognizing bit/byte as type keywords
- Fixed typed declarations for bit/byte/address types

### Syntax Highlighting
- Added `bit`, `byte`, `address` type highlighting
- Updated `%variable` snapshot highlighting (% pink, variable blue-pink)

---

## v4.6.7 (2026-01-14)

### New Features
- **HomeServer**: Local storage server for modules, projects and files
  - `includecpp server install` - Install and auto-start HomeServer
  - `includecpp server start/stop` - Manual server control
  - `includecpp server status` - Check server status
  - `includecpp server upload/download` - File and project management
  - `includecpp server list` - List stored items
  - `includecpp server delete` - Remove items
  - `includecpp server port` - Change server port
  - `includecpp server deinstall` - Remove HomeServer completely
- Server runs in background (no terminal window)
- Auto-start support on Windows
- SQLite database for metadata storage
- Default port: 2007

---

## v4.6.6 (2026-01-14)

### New Features
- **ENUM support**: Expose C++ enums to Python via `ENUM(EnumName) CLASS { values... }` syntax
- **Multiple SOURCE support**: `SOURCE(file1) && SOURCE(file2)` in .cp files
- **FIELD_ARRAY support**: C-style arrays now properly bound as read-only `bytes` properties
- Automatic detection of array fields in plugin command

### Bug Fixes
- Fixed signed/unsigned comparison warning from pybind11 enum bindings
- Removed SIGNED_UNSIGNED from error catalog (was a warning, not error)
- Fixed array fields causing `invalid array assignment` error
- Version display now shows X.X format in build output

### Breaking Changes
- Array fields in structs are now read-only (accessible as `bytes`)

---

## v4.3.2 (2026-01-08)

### New Features
- `embedded` keyword now supports enums: `embedded NewName &OldEnum { ... }`
- Enum values can be any expression (strings, numbers, etc.)
- `bytearrayed` list pattern matching: `case { ["read", "write"] }` matches list return values
- `bytearrayed` function references with parameters: `&checkAccess(10);`
- `bytearrayed` simulation mode: analyzes return values without executing function body (no side effects)
- `bytearrayed` now correctly handles conditional return paths (if/else)

### Bug Fixes
- Fixed `global` variables in namespaced payloads not being accessible via `@`
- Fixed `@module.function()` calls on `include()` results (ServiceDefinition support)
- Fixed `bytearrayed` case body return statements (CSSLReturn exception handling)
- Fixed embedded open define syntax: both `open embedded define` and `embedded open define` now work
- Fixed `switch(variable)` with param conditions: auto-detects param_switch when case uses `&` or `not`
- Fixed `bytearrayed` pattern parsing for boolean values (`true`/`false`)
- Enhanced param_switch conditions: `a & b`, `a & not b`, `a || b`, `a & !b` all supported
- param_switch now checks both kwargs AND OpenFind variables (positional args work with `case text:`)

---

## v4.3.0 (2026-01-08)

### New Features
- Payload namespace support: `payload("mylib", "libname")` loads definitions into `libname::`
- Auto-extension for payloads: `payload("engine")` finds `engine.cssl-pl`
- Namespaced class instantiation: `new Engine::GameEngine()`

### Bug Fixes
- Fixed try/catch parsing (catch was interpreted as function call)
- Added finally block support for try/catch
- Division by zero now throws error instead of returning 0
- Modulo by zero now throws error
- List index out of bounds now throws error with helpful message
- Dict key not found now throws error
- try/catch now catches Python exceptions
- Fixed `embedded &$PyObject::method` replacement (this-> now works)

---

## v4.2.5 (2026-01-08)

### New Features
- Added `embedded` keyword for immediate function/class replacement
- Added `switch` for open parameters with pattern matching

### Bug Fixes
- Fixed `OpenFind<type, "name">` returning function reference instead of value

---

## v4.2.4 (2026-01-08)

### Bug Fixes
- Fixed `%name` priority for `&function` overrides

---

## v4.2.3 (2026-01-08)

### Bug Fixes
- Removed pagination from CLI documentation
- Fixed `&builtin` function override

---

## v4.2.2 (2026-01-08)

### Bug Fixes
- Fixed bidirectional `lang$Instance` mutations

---

## v4.2.1 (2026-01-08)

### CLI Improvements
- `--doc` and `--changelog` now load from local files
- Added `--changelog --N` and `--changelog --all` options

---

## v4.2.0 (2026-01-08)

### New Features
- Multi-language support with `libinclude()` and `supports` keyword
- Cross-language instance sharing with `lang$InstanceName` syntax
- Language transformers for Python, JavaScript, Java, C#, C++
- SDK packages for C++, Java, C#, JavaScript
- Default parameter values in CSSL functions

### CLI
- Added `includecpp cssl sdk <lang>` command
- Added `--doc "searchterm"` for documentation search

---

## v4.1.0 (2024-12-15)

### New Features
- CodeInfusion system with `<<==` and `+<<==` operators
- Class `overwrites` keyword
- `super()` and `super::method()` calls
- New containers: `combo<T>`, `iterator<T>`, `datastruct<T>`
- `python::pythonize()` for returning CSSL classes to Python

---

## v4.0.3 (2024-11-20)

### New Features
- Universal instances with `instance<"name">`
- Python API: `getInstance()`, `createInstance()`, `deleteInstance()`
- Method injection with `+<<==`

---

## v4.0.2 (2024-11-01)

### New Features
- Simplified API: `CSSL.run()`, `CSSL.module()`, `CSSL.script()`
- Shared objects with `cssl.share(obj, "name")` and `$name` syntax

---

## v4.0.0 (2024-10-15)

### Major Release
- Complete rewrite of CSSL parser and runtime
- Generic container types: `stack<T>`, `vector<T>`, `map<K,V>`
- Class system with constructors and inheritance
- BruteInjection operators: `<==`, `+<==`, `-<==`
- Global variables with `@name`, captured variables with `%name`

---

## v3.2.0 (2024-09-01)

### New Features
- CPPY code conversion (`includecpp cppy convert`)
- AI-assisted conversion with `--ai` flag
- Fast incremental builds with `--fast` flag

---

## v3.1.0 (2024-08-01)

### New Features
- `includecpp auto` and `includecpp fix` commands
- `DEPENDS()` for module dependencies
- `TEMPLATE_FUNC()` for template instantiation

---

## v3.0.0 (2024-07-01)

### Initial Release
- C++ to Python binding generation
- CSSL scripting language
- Plugin file format (.cp)
- CMake-based build system
- Cross-platform support (Windows, Linux, Mac)
