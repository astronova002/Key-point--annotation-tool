import React, { useState } from 'react';
import { authService } from '../services/authService';

const AuthDebugger: React.FC = () => {
    const [output, setOutput] = useState<string[]>([]);

    const log = (message: any) => {
        const logMessage = typeof message === 'string' ? message : JSON.stringify(message, null, 2);
        setOutput(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${logMessage}`]);
        console.log(message);
    };

    const testLogin = async () => {
        try {
            log('Starting login test...');
            const user = await authService.login('admin', 'admin');
            log('Login successful:');
            log(user);
            
            // Check what's in localStorage
            const storedUser = localStorage.getItem('user');
            log('Stored user data:');
            log(storedUser ? JSON.parse(storedUser) : 'null');
            
        } catch (error) {
            log('Login error:');
            log(error);
        }
    };

    const testRefresh = async () => {
        try {
            log('Starting refresh test...');
            const result = await authService.refreshToken();
            log('Refresh successful:');
            log(result);
        } catch (error) {
            log('Refresh error:');
            log(error);
        }
    };

    const testGetUsers = async () => {
        try {
            log('Starting get users test...');
            const result = await authService.getUsers(1, 10, true);
            log('Get users successful:');
            log(result);
        } catch (error) {
            log('Get users error:');
            log(error);
        }
    };

    const checkLocalStorage = () => {
        const user = localStorage.getItem('user');
        log('Current localStorage:');
        log(user ? JSON.parse(user) : 'null');
        
        log('Has valid tokens:');
        log(authService.hasValidTokens());
        
        log('Current user:');
        log(authService.getCurrentUser());
    };

    const clearStorage = () => {
        localStorage.removeItem('user');
        log('Cleared localStorage');
    };

    const clearOutput = () => {
        setOutput([]);
    };

    return (
        <div style={{ padding: '20px', fontFamily: 'monospace' }}>
            <h2>Auth Debugger</h2>
            <div style={{ marginBottom: '20px' }}>
                <button onClick={testLogin} style={{ margin: '5px' }}>Test Login</button>
                <button onClick={testRefresh} style={{ margin: '5px' }}>Test Refresh</button>
                <button onClick={testGetUsers} style={{ margin: '5px' }}>Test Get Users</button>
                <button onClick={checkLocalStorage} style={{ margin: '5px' }}>Check Storage</button>
                <button onClick={clearStorage} style={{ margin: '5px' }}>Clear Storage</button>
                <button onClick={clearOutput} style={{ margin: '5px' }}>Clear Output</button>
            </div>
            <div style={{ 
                border: '1px solid #ccc', 
                padding: '10px', 
                height: '400px', 
                overflowY: 'auto',
                backgroundColor: '#f5f5f5',
                whiteSpace: 'pre-wrap'
            }}>
                {output.map((line, index) => (
                    <div key={index}>{line}</div>
                ))}
            </div>
        </div>
    );
};

export default AuthDebugger;
