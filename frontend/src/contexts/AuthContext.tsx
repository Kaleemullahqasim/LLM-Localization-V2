import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
  username: string;
  role: 'admin' | 'test-taker' | 'evaluator';
  name: string;
}

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => boolean;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Dummy users for MVP (in production, this would be a proper backend auth system)
const DUMMY_USERS = [
  { username: 'admin', password: 'admin123', role: 'admin' as const, name: 'Admin User' },
  { username: 'tester', password: 'test123', role: 'test-taker' as const, name: 'Test Taker' },
  { username: 'reviewer', password: 'review123', role: 'evaluator' as const, name: 'Evaluator' },
];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    // Check if user is already logged in (from localStorage)
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const login = (username: string, password: string): boolean => {
    const foundUser = DUMMY_USERS.find(
      u => u.username === username && u.password === password
    );

    if (foundUser) {
      const userData: User = {
        username: foundUser.username,
        role: foundUser.role,
        name: foundUser.name
      };
      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));
      return true;
    }
    return false;
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

