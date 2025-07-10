import React from 'react';
import packageJson from '../../package.json';

export const Version: React.FC = () => {
  return (
    <span className="text-xs text-muted-foreground ml-4">
      v{packageJson.version}
    </span>
  );
};

export default Version; 