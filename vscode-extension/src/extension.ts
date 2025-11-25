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

                const gateName = parts[startIndex-1];
                if (gateName !== 'measure' && numQubits > 0) {
                     for (let j = startIndex; j < parts.length; j++) {
                        const part = parts[j];
                        
                        // Skip variables (starting with $) to avoid false positives
                        if (part.startsWith('$')) {
                            continue;
                        }

                        // Check if it's a pure integer
                        if (/^\d+$/.test(part)) {
                            const idx = parseInt(part);
                            if (idx >= numQubits) {
                                const col = line.lastIndexOf(part); 
                                const range = new vscode.Range(i, col, i, col + part.length);
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
