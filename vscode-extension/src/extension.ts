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

    collection.set(document.uri, diagnostics);
}

export function deactivate() {}
