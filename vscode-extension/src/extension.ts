import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    console.log('QuYAML extension is now active!');

    const diagnosticCollection = vscode.languages.createDiagnosticCollection('quyaml');
    context.subscriptions.push(diagnosticCollection);

    context.subscriptions.push(
        vscode.workspace.onDidChangeTextDocument(event => {
            if (event.document.languageId === 'quyaml') {
                validateQuYaml(event.document, diagnosticCollection);
            }
        })
    );

    context.subscriptions.push(
        vscode.workspace.onDidOpenTextDocument(document => {
            if (document.languageId === 'quyaml') {
                validateQuYaml(document, diagnosticCollection);
            }
        })
    );

    if (vscode.window.activeTextEditor && vscode.window.activeTextEditor.document.languageId === 'quyaml') {
        validateQuYaml(vscode.window.activeTextEditor.document, diagnosticCollection);
    }
}

function validateQuYaml(document: vscode.TextDocument, collection: vscode.DiagnosticCollection) {
    const text = document.getText();
    const diagnostics: vscode.Diagnostic[] = [];

    const requiredKeys = ['version', 'circuit', 'qubits', 'bits', 'ops'];
    
    // Simple check: does the file contain these keys?
    // This is a very naive validator, but sufficient for a "simple extension" demo.
    // A real one would parse the YAML.
    
    requiredKeys.forEach(key => {
        if (!text.includes(key + ':')) {
            const diagnostic = new vscode.Diagnostic(
                new vscode.Range(0, 0, 0, 0),
                `Missing required key: ${key}`,
                vscode.DiagnosticSeverity.Error
            );
            diagnostics.push(diagnostic);
        }
    });

    // Check version
    if (text.includes("version:")) {
        const versionMatch = text.match(/version:\s*['"]?([\d.]+)['"]?/);
        if (versionMatch && versionMatch[1] !== '0.4') {
             // Find the line
             const index = versionMatch.index || 0;
             const position = document.positionAt(index);
             const range = new vscode.Range(position, position.translate(0, versionMatch[0].length));
             
             diagnostics.push(new vscode.Diagnostic(
                 range,
                 `Unsupported version: ${versionMatch[1]}. Expected '0.4'`,
                 vscode.DiagnosticSeverity.Warning
             ));
        }
    }

    // Qubit Counter Logic
    let numQubits = 0;
    const qubitsMatch = text.match(/qubits:\s*(?:q\[(\d+)\]|(\d+))/);
    if (qubitsMatch) {
        numQubits = parseInt(qubitsMatch[1] || qubitsMatch[2]);
    }

    // Classical Bit Counter Logic
    let numBits = 0;
    const bitsMatch = text.match(/(?:bits|creg):\s*(?:c\[(\d+)\]|(\d+))/);
    if (bitsMatch) {
        numBits = parseInt(bitsMatch[1] || bitsMatch[2]);
    }

    if (numQubits > 0 || numBits > 0) {
        const lines = text.split('\n');
        lines.forEach((line, i) => {
            // 1. Check structured ops: "q: 5" or "c: 5"
            const qMatch = line.match(/q:\s*(\d+)/);
            if (qMatch && numQubits > 0) {
                const idx = parseInt(qMatch[1]);
                if (idx >= numQubits) {
                    const startCol = line.indexOf(qMatch[1]);
                    const range = new vscode.Range(i, startCol, i, startCol + qMatch[1].length);
                    diagnostics.push(new vscode.Diagnostic(
                        range, 
                        `Qubit index ${idx} out of range (max ${numQubits - 1})`, 
                        vscode.DiagnosticSeverity.Error
                    ));
                }
            }

            const cMatch = line.match(/c:\s*(\d+)/);
            if (cMatch && numBits > 0) {
                const idx = parseInt(cMatch[1]);
                if (idx >= numBits) {
                    const startCol = line.indexOf(cMatch[1]);
                    const range = new vscode.Range(i, startCol, i, startCol + cMatch[1].length);
                    diagnostics.push(new vscode.Diagnostic(
                        range, 
                        `Classical bit index ${idx} out of range (max ${numBits - 1})`, 
                        vscode.DiagnosticSeverity.Error
                    ));
                }
            }

            // 2. Check inline ops: "- cx 0 5" or "- measure 0 5"
            const trimmed = line.trim();
            if (trimmed.startsWith('-')) {
                // Remove parameters like (0.5) to avoid false positives
                const noParams = trimmed.replace(/\([^)]*\)/g, '');
                const parts = noParams.split(/\s+/);
                
                // Skip the first part (the gate name, e.g., "- cx")
                let startIndex = 1;
                if (parts[0] === '-') startIndex = 2;

                // Heuristic: For 'measure', usually "measure q c" or "measure q -> c"
                // For gates, usually "gate q1 q2 ..."
                // This is a simple heuristic and might need refinement for complex cases.
                
                // Check for qubit indices in general gates
                // Note: This simple loop assumes all numbers are qubit indices, which is true for most gates
                // but NOT for measure (which has cbit) or if there are integer params (though we stripped parens).
                // Ideally we'd know the gate signature.
                
                // Special handling for measure if it looks like "- measure 0 1" (q=0, c=1)
                // But QuYAML parser often uses structured measure.
                // If user writes "- measure 0 1", parser might treat it as measure_all or error?
                // QuYAML parser: "measure" -> measure_all. "measure q c" -> not standard in parser unless custom?
                // Wait, parser `_apply_instruction` handles `measure` -> `measure_all`.
                // It does NOT seem to handle `measure 0 1` inline string in `_apply_instruction`.
                // It only handles `measure` (all) or structured `measure: ...`.
                // So we might not need to validate inline measure indices if they aren't valid syntax anyway.
                // However, let's keep the qubit check for gates like `cx 0 5`.
                
                const gateName = parts[startIndex-1];
                if (gateName !== 'measure' && numQubits > 0) {
                     for (let j = startIndex; j < parts.length; j++) {
                        // Check if it's a pure integer
                        if (/^\d+$/.test(parts[j])) {
                            const idx = parseInt(parts[j]);
                            if (idx >= numQubits) {
                                const col = line.lastIndexOf(parts[j]); 
                                const range = new vscode.Range(i, col, i, col + parts[j].length);
                                diagnostics.push(new vscode.Diagnostic(
                                    range, 
                                    `Qubit index ${idx} out of range (max ${numQubits - 1})`, 
                                    vscode.DiagnosticSeverity.Error
                                ));
                            }
                        }
                    }
                }
            }
        });
    }

    collection.set(document.uri, diagnostics);
}

export function deactivate() {}
