import React, { useState } from 'react';

function App() {
    const [count, setCount] = useState(0);

    return (
        <div className="min-h-screen bg-gray-100 flex items-center justify-center">
            <div className="bg-white p-8 rounded-xl shadow-lg">
                <h1 className="text-3xl font-bold text-gray-800 mb-4">Frontend Restored</h1>
                <p className="text-gray-600 mb-4">This is a placeholder for the restored React application.</p>
                <button
                    onClick={() => setCount(count + 1)}
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
                >
                    Count is {count}
                </button>
            </div>
        </div>
    );
}

export default App;
