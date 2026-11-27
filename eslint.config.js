import js from '@eslint/js';
import globals from 'globals';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import reactHooks from 'eslint-plugin-react-hooks';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  { ignores: ['**/dist/**', '**/node_modules/**', 'backend/**'] },
  js.configs.recommended,
  ...tseslint.configs.strict,
  {
    files: ['frontend/**/*.{ts,tsx}'],
    languageOptions: { globals: globals.browser },
    plugins: { 'react-hooks': reactHooks },
    rules: reactHooks.configs.recommended.rules,
  },
  {
    files: ['frontend/**/*.tsx'],
    ...jsxA11y.flatConfigs.recommended,
  },
  {
    files: ['*.js', '**/*.config.{js,ts}'],
    languageOptions: { globals: globals.node },
  },
);
