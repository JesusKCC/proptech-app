'use client';

import React from 'react';
import { RoleProvider } from '../../context/RoleContext';

export const Providers: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <RoleProvider initialRole="proyectos">{children}</RoleProvider>;
};
