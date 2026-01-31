# PyCharter UI

Standalone Next.js + React UI for PyCharter built with shadcn/ui.

## Features

- ✅ **shadcn/ui** - Modern, accessible component library
- ✅ **Next.js 14 App Router** - Latest Next.js features
- ✅ **TypeScript** - Full type safety
- ✅ **Tailwind CSS** - Utility-first styling
- ✅ **Navigation** - Built-in routing and navigation
- ✅ **Loading States** - Proper loading handling with Next.js conventions
- ✅ **Error Handling** - Comprehensive error boundaries and displays

## Installation

The UI is an optional component. Install it with:

```bash
pip install pycharter[ui]
```

Then install npm dependencies:

```bash
cd ui
npm install
```

## Development

### Prerequisites

- Node.js 18+ and npm
- PyCharter API server running (optional, but required for full functionality)

### Setup

1. Install dependencies:
   ```bash
   cd ui
   npm install
   ```

2. Create `.env.local`:
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. Run development server:
   ```bash
   pycharter ui dev
   # or
   npm run dev
   ```

   The UI will be available at `http://localhost:3000`

### Building for Production

1. Build the UI:
   ```bash
   pycharter ui build
   # or
   npm run build
   ```

2. Serve the built UI:
   ```bash
   pycharter ui serve
   ```

## Project Structure

```
ui/
├── src/
│   ├── app/              # Next.js App Router pages
│   │   ├── layout.tsx    # Root layout with navigation
│   │   ├── page.tsx      # Home/landing page
│   │   ├── loading.tsx   # Global loading state
│   │   ├── error.tsx     # Global error handler
│   │   └── [routes]/     # Route pages
│   ├── components/
│   │   ├── ui/           # shadcn/ui components
│   │   ├── Navigation.tsx
│   │   ├── ErrorBoundary.tsx
│   │   ├── ErrorDisplay.tsx
│   │   └── LoadingSpinner.tsx
│   ├── lib/
│   │   ├── api.ts        # API client
│   │   ├── types.ts      # TypeScript types
│   │   ├── constants.ts  # App constants
│   │   └── utils.ts      # Utility functions
│   └── hooks/
│       └── useApi.ts     # API hook with loading/error states
├── components.json       # shadcn/ui configuration
└── package.json
```

## Components

### shadcn/ui Components

- `Button` - Button component with variants
- `Card` - Card container with header, content, footer
- `Skeleton` - Loading skeleton component

### Custom Components

- `Navigation` - Top navigation bar with active route highlighting
- `ErrorBoundary` - React error boundary
- `ErrorDisplay` - API error display component
- `LoadingSpinner` - Loading spinner with sizes
- `PageLoading` - Full-page loading state
- `CardSkeleton` - Card loading skeleton
- `TableSkeleton` - Table loading skeleton

## Best Practices

### Loading States

Next.js 14 App Router provides automatic loading states:

1. **Route-level loading**: Create `loading.tsx` in route folders
2. **Component-level loading**: Use `PageLoading` or `LoadingSpinner`
3. **Skeleton screens**: Use `CardSkeleton` or `TableSkeleton` for better UX

### Error Handling

1. **Route-level errors**: Create `error.tsx` in route folders (automatically handled)
2. **Component-level errors**: Use `ErrorDisplay` component
3. **Global errors**: `ErrorBoundary` in root layout

### API Integration

Use the `useApi` hook for API calls:

```typescript
import { useApi } from '@/hooks/useApi';
import { api } from '@/lib/api';

const { data, loading, error, execute } = useApi(() => api.metadata.listSchemas());

useEffect(() => {
  execute();
}, [execute]);
```

## Adding shadcn/ui Components

To add more shadcn/ui components:

```bash
npx shadcn-ui@latest add [component-name]
```

Example:
```bash
npx shadcn-ui@latest add input
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add table
```

## Configuration

- `components.json` - shadcn/ui configuration
- `tailwind.config.js` - Tailwind CSS configuration
- `tsconfig.json` - TypeScript configuration
- `.env.local` - Environment variables

## API Integration

The UI proxies API requests to the PyCharter API:
- In development: Next.js rewrites handle proxying
- In production: FastAPI server handles proxying

Make sure the PyCharter API server is running for the UI to function properly.

## Development with Cursor & v0

This UI is optimized for development with:
- **Cursor** - AI-powered code editor
- **v0** - Vercel's AI UI component generator

v0 generates shadcn/ui components that work seamlessly with this setup.
