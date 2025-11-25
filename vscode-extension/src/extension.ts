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

    if (numQubits > 0) {
        const lines = text.split('\n');
        lines.forEach((line, i) => {
            // 1. Check structured ops: "q: 5"
            const qMatch = line.match(/q:\s*(\d+)/);
            if (qMatch) {
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

            // 2. Check inline ops: "- cx 0 5"
            const trimmed = line.trim();
            if (trimmed.startsWith('-')) {
                // Remove parameters like (0.5) to avoid false positives
                const noParams = trimmed.replace(/\([^)]*\)/g, '');
                const parts = noParams.split(/\s+/);
                
                // Skip the first part (the gate name, e.g., "- cx")
                // Note: parts[0] is "-", parts[1] is "cx" usually, or parts[0] is "-cx"
                let startIndex = 1;
                if (parts[0] === '-') startIndex = 2;

                for (let j = startIndex; j < parts.length; j++) {
                    // Check if it's a pure integer
                    if (/^\d+$/.test(parts[j])) {
                        const idx = parseInt(parts[j]);
                        if (idx >= numQubits) {
                            // Find position in original line
                            // Note: This is naive and might match the wrong occurrence if duplicates exist
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
        });
    }

    collection.set(document.uri, diagnostics);
}

export function deactivate() {}
