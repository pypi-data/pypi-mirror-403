---
title: Interactive Demo
description: "Try nestedutils Python library in your browser. No installation required. Test dot-notation access to nested dictionaries and lists. Safely get, set, delete, and check existence of values in complex nested data structures."
keywords:
  - interactive demo
  - test nested data access
  - online nested utils
  - try nestedutils
  - browser demo
  - test dot notation
  - validate nested paths
  - test get_at set_at
  - nested dictionary demo
  - nested list demo
---

# Interactive Demo

Try the `nestedutils` library directly in your browser! This page uses [Pyodide](https://pyodide.org/) to run Python in the browser.

<div id="package-info" style="display: none; margin: 20px 0; padding: 15px; background: #e3f2fd; border-left: 4px solid #1976d2; border-radius: 4px;">
  <p style="margin: 0;"><strong>Installed package:</strong> <code>nestedutils</code> <span id="package-version"></span></p>
</div>

<div id="pyodide-loading" style="text-align: center; padding: 20px;">
  <p>Loading Pyodide...</p>
  <div class="spinner"></div>
</div>

<div id="test-interface" style="display: none;">
  <div class="test-section">
    <h3>Data Source</h3>
    <p style="color: #666; font-size: 0.9em; margin-bottom: 15px;">Select an example or edit the JSON directly. Valid JSON is automatically applied when you stop typing.</p>
    
    <!-- Horizontal Radio Buttons -->
    <div style="display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; align-items: center;">
      <label style="display: flex; align-items: center; gap: 6px; cursor: pointer; padding: 6px 0;" onmouseover="this.style.opacity='0.7'" onmouseout="this.style.opacity='1'">
        <input type="radio" name="data-source" value="example1" id="radio-example1" style="cursor: pointer;" />
        <span>Example 1: User Profile</span>
      </label>
      <label style="display: flex; align-items: center; gap: 6px; cursor: pointer; padding: 6px 0;" onmouseover="this.style.opacity='0.7'" onmouseout="this.style.opacity='1'">
        <input type="radio" name="data-source" value="example2" id="radio-example2" style="cursor: pointer;" />
        <span>Example 2: E-commerce Data</span>
      </label>
      <label style="display: flex; align-items: center; gap: 6px; cursor: pointer; padding: 6px 0;" onmouseover="this.style.opacity='0.7'" onmouseout="this.style.opacity='1'">
        <input type="radio" name="data-source" value="example3" id="radio-example3" style="cursor: pointer;" />
        <span>Example 3: API Response</span>
      </label>
      <label style="display: flex; align-items: center; gap: 6px; cursor: pointer; padding: 6px 0;" onmouseover="this.style.opacity='0.7'" onmouseout="this.style.opacity='1'">
        <input type="radio" name="data-source" value="custom" id="radio-custom" style="cursor: pointer;" />
        <span>Custom JSON</span>
      </label>
    </div>
    
    <!-- JSON Textarea -->
    <div style="position: relative;">
      <div id="json-status" style="position: absolute; top: 10px; right: 10px; font-size: 0.85em; font-weight: 500; z-index: 1;"></div>
      <textarea 
        id="custom-json-input" 
        placeholder='Enter valid JSON here, e.g., {"key": "value"}'
        style="width: 100%; min-height: 300px; padding: 12px; border: 1px solid #ccc; border-radius: 4px; font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace; font-size: 0.9em; resize: vertical; line-height: 1.5; tab-size: 2;"
      ></textarea>
      <div id="json-error" style="margin-top: 8px; font-size: 0.85em; min-height: 20px; font-family: monospace;"></div>
    </div>
  </div>

  <div class="test-section" style="margin-top: 30px;">
    <h3>1. Get Value (get_at)</h3>
    <p>Retrieve a value from the nested data structure using dot notation:</p>
    <div style="display: flex; gap: 10px; margin-bottom: 10px; flex-wrap: wrap;">
      <input 
        type="text" 
        id="get-path" 
        placeholder="e.g., user.profile.name or items.0.title"
        style="flex: 1; min-width: 250px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"
      />
      <input 
        type="text" 
        id="get-default" 
        placeholder="Default value (optional)"
        style="flex: 0 0 150px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"
      />
      <button 
        id="get-btn" 
        style="padding: 8px 16px; background: #1976d2; color: white; border: none; border-radius: 4px; cursor: pointer;"
      >
        Get Value
      </button>
    </div>
    <div id="get-result" style="margin-top: 10px; padding: 10px; background: #f5f5f5; border-radius: 4px; min-height: 30px;"></div>
  </div>

  <div class="test-section" style="margin-top: 30px;">
    <h3>2. Set Value (set_at)</h3>
    <p>Set a value in the nested data structure. Missing containers will be created automatically:</p>
    <div style="display: flex; gap: 10px; margin-bottom: 10px; flex-wrap: wrap;">
      <input 
        type="text" 
        id="set-path" 
        placeholder="e.g., user.profile.email or items.2.name"
        style="flex: 1; min-width: 200px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"
      />
      <input 
        type="text" 
        id="set-value" 
        placeholder="Value to set"
        style="flex: 1; min-width: 150px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"
      />
      <select 
        id="set-strategy" 
        style="flex: 0 0 120px; padding: 8px; border: 1px solid #ccc; border-radius: 4px; background: white;"
      >
        <option value="auto">auto</option>
        <option value="none">none</option>
        <option value="dict">dict</option>
        <option value="list">list</option>
      </select>
      <button 
        id="set-btn" 
        style="padding: 8px 16px; background: #1976d2; color: white; border: none; border-radius: 4px; cursor: pointer;"
      >
        Set Value
      </button>
    </div>
    <p style="color: #666; font-size: 0.85em; margin-top: 5px;">
      <strong>Fill Strategy:</strong> <code>auto</code> (smart defaults), <code>none</code> (fill gaps with None), 
      <code>dict</code> (always create dicts), <code>list</code> (always create lists)
    </p>
    <div id="set-result" style="margin-top: 10px; padding: 10px; background: #f5f5f5; border-radius: 4px; min-height: 30px;"></div>
  </div>

  <div class="test-section" style="margin-top: 30px;">
    <h3>3. Check Existence (exists_at)</h3>
    <p>Check if a path exists in the nested data structure:</p>
    <div style="display: flex; gap: 10px; margin-bottom: 10px;">
      <input 
        type="text" 
        id="exists-path" 
        placeholder="e.g., user.profile.name or items.0.title"
        style="flex: 1; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"
      />
      <button 
        id="exists-btn" 
        style="padding: 8px 16px; background: #1976d2; color: white; border: none; border-radius: 4px; cursor: pointer;"
      >
        Check
      </button>
    </div>
    <div id="exists-result" style="margin-top: 10px; padding: 10px; background: #f5f5f5; border-radius: 4px; min-height: 30px;"></div>
  </div>

  <div class="test-section" style="margin-top: 30px;">
    <h3>4. Delete Value (delete_at)</h3>
    <p>Delete a value from the nested data structure:</p>
    <div style="display: flex; gap: 10px; margin-bottom: 10px; flex-wrap: wrap;">
      <input 
        type="text" 
        id="delete-path" 
        placeholder="e.g., user.profile.email or items.1"
        style="flex: 1; min-width: 200px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"
      />
      <label style="display: flex; align-items: center; gap: 5px; padding: 8px;">
        <input type="checkbox" id="delete-allow-list" />
        <span style="font-size: 0.9em;">Allow list mutation</span>
      </label>
      <button 
        id="delete-btn" 
        style="padding: 8px 16px; background: #1976d2; color: white; border: none; border-radius: 4px; cursor: pointer;"
      >
        Delete
      </button>
    </div>
    <div id="delete-result" style="margin-top: 10px; padding: 10px; background: #f5f5f5; border-radius: 4px; min-height: 30px;"></div>
  </div>

</div>

<style>
  .test-section {
    border: 1px solid #e0e0e0;
    padding: 20px;
    border-radius: 8px;
    background: white;
  }
  
  .spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #1976d2;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 1s linear infinite;
    margin: 20px auto;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .result-success {
    color: #2e7d32;
    font-weight: bold;
  }
  
  .result-error {
    color: #c62828;
    font-weight: bold;
  }
  
  .result-info {
    color: #1976d2;
  }
  
  button:hover {
    background: #1565c0 !important;
  }
  
  button:active {
    background: #0d47a1 !important;
  }
  
  #reset-btn:hover {
    background: #616161 !important;
  }
  
  #reset-btn:active {
    background: #424242 !important;
  }
  
  select {
    cursor: pointer;
  }
  
  select:focus, input:focus, textarea:focus {
    outline: 2px solid #1976d2;
    outline-offset: 2px;
  }
  
  #json-error {
    font-family: monospace;
    font-size: 0.85em;
  }
  
  #json-status {
    font-weight: 500;
  }
  
  textarea {
    line-height: 1.5;
  }
  
  @media (max-width: 768px) {
    .test-section > div[style*="display: flex"] {
      flex-direction: column !important;
    }
  }
</style>

<script src="https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js"></script>

<script type="text/javascript">
  let pyodide;
  let appliedJsonString = ""; // Track the currently applied JSON
  let autoApplyTimer = null; // Debounce timer for auto-apply

  async function main() {
    // Load Pyodide
    pyodide = await loadPyodide({
      indexURL: "https://cdn.jsdelivr.net/pyodide/v0.24.1/full/"
    });
    
    // Update loading message
    document.getElementById("pyodide-loading").innerHTML = "<p>Installing nestedutils package...</p>";
    
    // Install nestedutils package
    await pyodide.loadPackage("micropip");
    const micropip = pyodide.pyimport("micropip");
    await micropip.install("nestedutils");
    
    // Import functions and initialize data
    pyodide.runPython(`
      from nestedutils import get_at, set_at, delete_at, exists_at
      import json
      
      # Initialize data structure
      data = {}
      
      # Try to get package version
      try:
          import importlib.metadata
          package_version = importlib.metadata.version('nestedutils')
      except:
          try:
              import importlib_metadata
              package_version = importlib_metadata.version('nestedutils')
          except:
              package_version = "unknown"
    `);
    
    const packageVersion = pyodide.globals.get("package_version");
    
    // Display package version
    if (packageVersion && packageVersion !== "unknown") {
      document.getElementById("package-version").textContent = `v${packageVersion}`;
      document.getElementById("package-info").style.display = "block";
    }
    
    // Initialize data structure display
    updateDataDisplay(true); // Sync textarea on initial load
    
    // Set initial radio button state
    document.getElementById("radio-custom").checked = true;
    
    // Initialize applied state
    const initialJson = document.getElementById("custom-json-input").value.trim();
    if (initialJson) {
      try {
        appliedJsonString = JSON.stringify(JSON.parse(initialJson));
      } catch (e) {
        appliedJsonString = "";
      }
    } else {
      appliedJsonString = "{}";
    }
    
    // Hide loading, show interface
    document.getElementById("pyodide-loading").style.display = "none";
    document.getElementById("test-interface").style.display = "block";
    
    // Setup event listeners
    setupEventListeners();
  }

  function updateDataDisplay(syncTextarea = false) {
    // Sync JSON editor with current data structure when loading examples
    if (syncTextarea) {
      try {
        const json = pyodide.runPython(`json.dumps(data, indent=2)`);
        const jsonStr = json || "{}";
        const customInput = document.getElementById("custom-json-input");
        customInput.value = jsonStr;
        // Update applied state to match current data
        appliedJsonString = JSON.stringify(JSON.parse(jsonStr));
        // Clear any error messages and update status
        document.getElementById("json-error").textContent = "";
        updateJsonStatus(true);
      } catch (error) {
        console.error("Error updating display:", error);
      }
    }
  }
  
  // Check if there are unsaved changes (for auto-apply)
  function hasUnsavedChanges() {
    const jsonInput = document.getElementById("custom-json-input").value.trim();
    
    // Handle empty input
    if (!jsonInput) {
      // Empty input matches empty applied state or {}
      return appliedJsonString !== "" && appliedJsonString !== "{}";
    }
    
    // Handle empty object/array strings
    if (jsonInput === "{}" || jsonInput === "[]") {
      const normalized = jsonInput;
      return normalized !== appliedJsonString;
    }
    
    try {
      // Normalize both for comparison (handles formatting differences)
      const normalized = JSON.stringify(JSON.parse(jsonInput));
      // Compare normalized strings
      return normalized !== appliedJsonString;
    } catch {
      // If invalid JSON, consider it as having changes
      return true;
    }
  }
  
  // Apply JSON function (auto-apply only)
  function applyJsonData() {
    const jsonInput = document.getElementById("custom-json-input").value.trim();
    const errorDiv = document.getElementById("json-error");
    
    if (!jsonInput) {
      updateJsonStatus(false, "Please enter JSON data");
      errorDiv.textContent = "Please enter JSON data";
      errorDiv.style.color = "#c62828";
      return;
    }
    
    // Validate JSON
    let parsedData;
    try {
      parsedData = JSON.parse(jsonInput);
    } catch (error) {
      updateJsonStatus(false, "Invalid JSON");
      errorDiv.textContent = `Invalid JSON: ${error.message}`;
      errorDiv.style.color = "#c62828";
      return;
    }
    
    // Validate that it's an object or array (not primitive)
    if (typeof parsedData !== "object" || parsedData === null) {
      updateJsonStatus(false, "Must be object or array");
      errorDiv.textContent = "JSON must be an object {} or array []";
      errorDiv.style.color = "#c62828";
      return;
    }
    
    // Set the data in Python
    try {
      const jsonStr = JSON.stringify(parsedData);
      pyodide.runPython(`data = json.loads(${JSON.stringify(jsonStr)})`);
      appliedJsonString = jsonStr; // Update applied state
      clearResults();
      updateJsonStatus(true, "✓ Applied");
      errorDiv.textContent = "";
      document.getElementById("radio-custom").checked = true;
    } catch (error) {
      updateJsonStatus(false, "Error applying");
      errorDiv.textContent = `Error setting data: ${error.message}`;
      errorDiv.style.color = "#c62828";
    }
  }

  function setupEventListeners() {
    // Note: Removed "Reset to Empty" button - users can just clear the JSON editor or set it to {}
    
    // Radio button change handlers
    const radioButtons = document.querySelectorAll('input[name="data-source"]');
    radioButtons.forEach(radio => {
      radio.addEventListener("change", (e) => {
        const value = e.target.value;
        if (value === "custom") {
          // Don't auto-load, just switch to custom mode
          return;
        }
        loadExampleData(value);
      });
    });
    
    // Load example data function
    function loadExampleData(exampleType) {
      let exampleCode = "";
      
      switch(exampleType) {
        case "example1":
          // Example 1: User Profile
          exampleCode = `
        data = {
          "user": {
            "name": "John Doe",
            "age": 30,
            "profile": {
              "email": "john@example.com",
                  "bio": "Software developer",
                  "address": {
                    "street": "123 Main St",
                    "city": "San Francisco",
                    "zip": "94102"
                  }
                },
                "preferences": {
                  "theme": "dark",
                  "notifications": True,
                  "language": "en"
            }
          },
          "items": [
            {"id": 1, "title": "First Item", "tags": ["python", "demo"]},
            {"id": 2, "title": "Second Item", "tags": ["javascript"]}
              ]
            }
          `;
          break;
        case "example2":
          // Example 2: E-commerce Data
          exampleCode = `
            data = {
              "store": {
                "name": "TechShop",
                "location": "New York"
              },
              "products": [
                {
                  "id": 101,
                  "name": "Laptop",
                  "price": 999.99,
                  "inventory": {
                    "stock": 45,
                    "warehouse": "A1"
                  },
                  "reviews": [
                    {"rating": 5, "comment": "Great product!"},
                    {"rating": 4, "comment": "Good value"}
                  ]
                },
                {
                  "id": 102,
                  "name": "Mouse",
                  "price": 29.99,
                  "inventory": {
                    "stock": 120,
                    "warehouse": "B2"
                  },
                  "reviews": []
                }
              ],
              "orders": [
                {
                  "order_id": "ORD-001",
                  "customer": "Alice",
                  "items": ["101", "102"],
                  "total": 1029.98
                }
              ]
            }
          `;
          break;
        case "example3":
          // Example 3: API Response
          exampleCode = `
            data = {
              "status": "success",
              "data": {
                "users": [
                  {
                    "id": 1,
                    "username": "alice",
                    "metadata": {
                      "created_at": "2024-01-15",
                      "last_login": "2024-12-01"
                    },
                    "roles": ["admin", "user"]
                  },
                  {
                    "id": 2,
                    "username": "bob",
                    "metadata": {
                      "created_at": "2024-02-20",
                      "last_login": None
                    },
                    "roles": ["user"]
                  }
                ],
                "pagination": {
                  "page": 1,
                  "per_page": 10,
                  "total": 2
                }
              },
              "errors": []
            }
          `;
          break;
      }
      
      if (exampleCode) {
        pyodide.runPython(exampleCode);
        updateDataDisplay(true); // Sync textarea when loading examples
        clearResults();
        updateJsonStatus(true, "✓ Example loaded");
        // Check the corresponding radio button
        document.getElementById(`radio-${exampleType}`).checked = true;
        // Update applied state to match loaded example
        const jsonInput = document.getElementById("custom-json-input").value.trim();
        if (jsonInput) {
          try {
            appliedJsonString = JSON.stringify(JSON.parse(jsonInput));
          } catch (e) {
            appliedJsonString = "";
          }
        }
      }
    }
    
    // Update JSON status indicator
    function updateJsonStatus(isValid, message = null) {
      const statusDiv = document.getElementById("json-status");
      const errorDiv = document.getElementById("json-error");
      
      if (message !== null) {
        statusDiv.textContent = message;
        statusDiv.style.color = isValid ? "#2e7d32" : "#c62828";
      } else if (isValid === true) {
        statusDiv.textContent = "✓ Valid JSON";
        statusDiv.style.color = "#2e7d32";
        errorDiv.textContent = "";
      } else if (isValid === false) {
        statusDiv.textContent = "✗ Invalid JSON";
        statusDiv.style.color = "#c62828";
      } else {
        // Clear status
        statusDiv.textContent = "";
        errorDiv.textContent = "";
      }
    }
    
    // Real-time JSON validation and auto-apply on input
    document.getElementById("custom-json-input").addEventListener("input", () => {
      const jsonInput = document.getElementById("custom-json-input").value.trim();
      const errorDiv = document.getElementById("json-error");
      
      // Switch to custom mode when user starts editing
      if (jsonInput) {
        document.getElementById("radio-custom").checked = true;
      }
      
      // Clear any existing auto-apply timer
      if (autoApplyTimer) {
        clearTimeout(autoApplyTimer);
        autoApplyTimer = null;
      }
      
      if (!jsonInput) {
        updateJsonStatus(null);
        errorDiv.textContent = "";
        return;
      }
      
      // Validate JSON
      let isValid = false;
      try {
        const parsed = JSON.parse(jsonInput);
        if (typeof parsed !== "object" || parsed === null) {
          updateJsonStatus(false);
          errorDiv.textContent = "JSON must be an object {} or array []";
          errorDiv.style.color = "#c62828";
          isValid = false;
        } else {
          updateJsonStatus(true);
          errorDiv.textContent = "";
          isValid = true;
        }
      } catch (error) {
        updateJsonStatus(false);
        errorDiv.textContent = `Invalid JSON: ${error.message}`;
        errorDiv.style.color = "#c62828";
        isValid = false;
      }
      
      // Auto-apply valid JSON after user stops typing (1 second delay)
      if (isValid) {
        autoApplyTimer = setTimeout(() => {
          // Only auto-apply if JSON is still valid and different from applied
          if (hasUnsavedChanges()) {
            applyJsonData();
          }
        }, 1000); // 1 second debounce
      }
    });
    
    // Get value
    document.getElementById("get-btn").addEventListener("click", async () => {
      const path = document.getElementById("get-path").value.trim();
      const defaultValue = document.getElementById("get-default").value.trim();
      const resultDiv = document.getElementById("get-result");
      
      if (!path) {
        resultDiv.innerHTML = '<span class="result-error">Please enter a path</span>';
        return;
      }
      
      try {
        resultDiv.innerHTML = '<span class="result-info">Processing...</span>';
        
        let code = `get_at(data, ${JSON.stringify(path)}`;
        if (defaultValue) {
          // Try to parse as appropriate type
          let defaultVal = defaultValue;
          if (defaultValue === "null" || defaultValue === "None") {
            defaultVal = null;
          } else if (!isNaN(defaultValue) && defaultValue !== "") {
            defaultVal = Number(defaultValue);
          } else if (defaultValue === "true" || defaultValue === "True") {
            defaultVal = true;
          } else if (defaultValue === "false" || defaultValue === "False") {
            defaultVal = false;
          }
          code += `, default=${JSON.stringify(defaultVal)}`;
        }
        code += `)`;
        
        const result = pyodide.runPython(code);
        
        // Format the result for display
        let resultStr;
        try {
          resultStr = pyodide.runPython(`json.dumps(${JSON.stringify(result)})`);
        } catch (e) {
          resultStr = String(result);
        }
        
        if (result === null || result === undefined) {
          resultDiv.innerHTML = `<span class="result-info">Result: <code>null</code></span>`;
        } else {
          resultDiv.innerHTML = `<span class="result-success">Value found:</span><br><code style="background: white; padding: 5px; border-radius: 3px; display: inline-block; margin-top: 5px; font-family: monospace;">${escapeHtml(resultStr)}</code>`;
        }
      } catch (error) {
        resultDiv.innerHTML = `<span class="result-error">Error: ${escapeHtml(error.message)}</span>`;
      }
    });
    
    // Set value
    document.getElementById("set-btn").addEventListener("click", async () => {
      const path = document.getElementById("set-path").value.trim();
      const value = document.getElementById("set-value").value.trim();
      const strategy = document.getElementById("set-strategy").value;
      const resultDiv = document.getElementById("set-result");
      
      if (!path || value === "") {
        resultDiv.innerHTML = '<span class="result-error">Please enter a path and value</span>';
        return;
      }
      
      try {
        resultDiv.innerHTML = '<span class="result-info">Processing...</span>';
        
        // Try to parse value as appropriate type
        let parsedValue = value;
        if (value === "null" || value === "None") {
          parsedValue = null;
        } else if (!isNaN(value) && value !== "") {
          parsedValue = Number(value);
        } else if (value === "true" || value === "True") {
          parsedValue = true;
        } else if (value === "false" || value === "False") {
          parsedValue = false;
        } else {
          // Try to parse as JSON array or object
          try {
            parsedValue = JSON.parse(value);
          } catch (e) {
            // Keep as string
            parsedValue = value;
          }
        }
        
        pyodide.runPython(`set_at(data, ${JSON.stringify(path)}, ${JSON.stringify(parsedValue)}, fill_strategy=${JSON.stringify(strategy)})`);
        updateDataDisplay(true);
        resultDiv.innerHTML = `<span class="result-success">✓ Value set successfully</span>`;
      } catch (error) {
        resultDiv.innerHTML = `<span class="result-error">Error: ${escapeHtml(error.message)}</span>`;
      }
    });
    
    // Check existence
    document.getElementById("exists-btn").addEventListener("click", async () => {
      const path = document.getElementById("exists-path").value.trim();
      const resultDiv = document.getElementById("exists-result");
      
      if (!path) {
        resultDiv.innerHTML = '<span class="result-error">Please enter a path</span>';
        return;
      }
      
      try {
        resultDiv.innerHTML = '<span class="result-info">Processing...</span>';
        const exists = pyodide.runPython(`exists_at(data, ${JSON.stringify(path)})`);
        
        if (exists) {
          resultDiv.innerHTML = `<span class="result-success">✓ Path exists</span>`;
        } else {
          resultDiv.innerHTML = `<span class="result-info">Path does not exist</span>`;
        }
      } catch (error) {
        resultDiv.innerHTML = `<span class="result-error">Error: ${escapeHtml(error.message)}</span>`;
      }
    });
    
    // Delete value
    document.getElementById("delete-btn").addEventListener("click", async () => {
      const path = document.getElementById("delete-path").value.trim();
      const allowListMutation = document.getElementById("delete-allow-list").checked;
      const resultDiv = document.getElementById("delete-result");
      
      if (!path) {
        resultDiv.innerHTML = '<span class="result-error">Please enter a path</span>';
        return;
      }
      
      try {
        resultDiv.innerHTML = '<span class="result-info">Processing...</span>';
        const deleted = pyodide.runPython(`delete_at(data, ${JSON.stringify(path)}, allow_list_mutation=${allowListMutation ? 'True' : 'False'})`);
        updateDataDisplay(true);
        
        // Format the deleted value for display
        let deletedStr;
        try {
          deletedStr = pyodide.runPython(`json.dumps(${JSON.stringify(deleted)})`);
        } catch (e) {
          // If JSON serialization fails, convert to string
          deletedStr = String(deleted);
        }
        
        resultDiv.innerHTML = `<span class="result-success">✓ Value deleted:</span><br><code style="background: white; padding: 5px; border-radius: 3px; display: inline-block; margin-top: 5px; font-family: monospace;">${escapeHtml(deletedStr)}</code>`;
      } catch (error) {
        resultDiv.innerHTML = `<span class="result-error">Error: ${escapeHtml(error.message)}</span>`;
      }
    });
    
    // Allow Enter key to trigger actions
    document.getElementById("get-path").addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        document.getElementById("get-btn").click();
      }
    });
    
    document.getElementById("set-path").addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        document.getElementById("set-btn").click();
      }
    });
    
    document.getElementById("exists-path").addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        document.getElementById("exists-btn").click();
      }
    });
    
    document.getElementById("delete-path").addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        document.getElementById("delete-btn").click();
      }
    });
  }

  function clearResults() {
    document.getElementById("get-result").innerHTML = "";
    document.getElementById("set-result").innerHTML = "";
    document.getElementById("exists-result").innerHTML = "";
    document.getElementById("delete-result").innerHTML = "";
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  // Start loading Pyodide when page is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      main().catch(err => {
        document.getElementById("pyodide-loading").innerHTML = 
          `<p style="color: #c62828;">Error loading Pyodide: ${err.message}</p>`;
        console.error(err);
      });
    });
  } else {
    main().catch(err => {
      document.getElementById("pyodide-loading").innerHTML = 
        `<p style="color: #c62828;">Error loading Pyodide: ${err.message}</p>`;
      console.error(err);
    });
  }
</script>
