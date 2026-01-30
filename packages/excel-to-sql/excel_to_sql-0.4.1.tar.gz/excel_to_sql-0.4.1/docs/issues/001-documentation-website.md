# Add Documentation Website with Fumadocs

## Context

The excel-to-sql project has grown significantly with v0.3.0, introducing the Auto-Pilot Mode with 8 major features and 5 new components. The README is now 700+ lines and becoming difficult to navigate efficiently.

### Current State
- README.md: 700+ lines covering all features
- Comprehensive but linear navigation (Ctrl+F only)
- No visual examples or interactive demos
- Single file for all documentation
- No version-specific documentation

### Problem Statement
As the project matures and feature set expands, users need:
1. **Searchable documentation** - Find specific features quickly
2. **Visual examples** - See CLI output, Rich terminal displays
3. **Structured navigation** - Browse by topic (CLI, SDK, Auto-Pilot)
4. **Versioned docs** - Access documentation for specific versions
5. **Interactive examples** - Copy-paste code snippets with syntax highlighting

## 🎯 Proposed Solution

Implement a documentation website using **Fumadocs** - a modern, fast documentation framework.

### Why Fumadocs?

**Advantages:**
- ✅ **MDX Support** - Rich content with React components
- ✅ **Fast** - Built on Next.js for optimal performance
- ✅ **Search** - Full-text search out of the box
- ✅ **Modern UI** - Beautiful default theme with dark mode
- ✅ **Versioning** - Built-in support for multiple versions
- ✅ **Syntax Highlighting** - Perfect for Python/CLI examples
- ✅ **Free Hosting** - Deploy to Vercel at no cost

**Alternatives Considered:**
| Solution | Pros | Cons | Score |
|----------|------|------|-------|
| **Fumadocs** | Modern, fast, MDX, search | Requires React setup | ⭐⭐⭐⭐⭐ |
| ReadTheDocs | Python standard, widely used | Less modern, Sphinx complexity | ⭐⭐⭐ |
| GitHub Pages | Simple, free | Basic features, Jekyll limitations | ⭐⭐ |
| Docusaurus | Mature, popular | Heavier, slower build times | ⭐⭐⭐⭐ |

## 📐 Proposed Structure

```
documentation/
├── getting-started/
│   ├── installation.mdx          # pip install, uv, from source
│   ├── quick-start.mdx           # First import in 5 minutes
│   └── first-import.mdx          # Complete walkthrough
│
├── auto-pilot/
│   ├── overview.mdx              # What is Auto-Pilot Mode
│   ├── pattern-detection.mdx     # PatternDetector deep dive
│   ├── quality-scoring.mdx       # QualityScorer guide
│   ├── recommendations.mdx        # RecommendationEngine usage
│   ├── auto-fix.mdx              # AutoFixer capabilities
│   └── interactive-mode.mdx      # InteractiveWizard tutorial
│
├── cli-reference/
│   ├── overview.mdx              # CLI introduction
│   ├── init.mdx                  # Initialize project
│   ├── import.mdx                # Import Excel files
│   ├── export.mdx                # Export to Excel
│   ├── magic.mdx                 # Auto-Pilot command
│   ├── config.mdx                # Manage configurations
│   └── profile.mdx               # Data profiling
│
├── python-sdk/
│   ├── basics.mdx                # SDK introduction
│   ├── transformations.mdx        # Value mappings, calculated columns
│   ├── validators.mdx            # Custom validators
│   └── advanced.mdx               # Hooks, metadata
│
├── examples/
│   ├── e-commerce.mdx            # E-commerce dataset example
│   ├── data-migration.mdx        # Legacy system migration
│   └── automation.mdx            # CI/CD integration
│
├── api-reference/
│   ├── cli.mdx                   # CLI API docs
│   ├── sdk.mdx                   # Python SDK API
│   └── auto-pilot.mdx            # Auto-Pilot components API
│
└── changelog/
    ├── v0.3.0.mdx                # Latest release notes
    ├── v0.2.0.mdx                # Previous versions
    └── migration-guides.mdx      # Upgrade guides
```

## 🎨 Key Features to Implement

### 1. **Homepage**
- Hero section with quick start
- Feature highlights (Auto-Pilot, Transformations, Validation)
- Links to getting started
- PyPI installation badge

### 2. **Interactive Examples**
- Code blocks with copy button
- Terminal output simulation (Rich displays)
- Before/after comparisons
- Collapsible sections for advanced content

### 3. **Navigation**
- Sidebar with table of contents
- Breadcrumbs for current location
- Previous/next page navigation
- Search bar (Algolia or local search)

### 4. **Version Selector**
- Dropdown to switch between versions (v0.3.0, v0.2.0, main)
- "Latest version" banner on old docs
- Migration guides between versions

### 5. **Dark Mode**
- Toggle between light/dark themes
- Respects system preference
- Smooth transitions

### 6. **Visual Enhancements**
- Screenshots of CLI output (actual terminal captures)
- Architecture diagrams (Mermaid or similar)
- Component relationship diagrams
- Flowcharts for Auto-Pilot workflow

## 📝 Content Migration Plan

### Phase 1: Core Content (Priority: HIGH)
Migrate from README.md:
- Installation instructions
- Quick start guide
- CLI commands overview
- Python SDK basics
- Auto-Pilot introduction

### Phase 2: Deep Dives (Priority: MEDIUM)
Expand with detailed guides:
- Auto-Pilot components (PatternDetector, QualityScorer, etc.)
- Transformation types
- Validation system
- Configuration reference

### Phase 3: Examples & API (Priority: LOW)
Add practical content:
- Real-world examples
- API reference (auto-generated from docstrings)
- Troubleshooting guide
- FAQ section

## 🛠️ Technical Implementation

### Setup Steps

```bash
# 1. Initialize Fumadocs app
npm create fumadocs-app excel-to-sql-docs

# 2. Choose options
# Framework: Next.js
# Content source: Fumadocs MDX

# 3. Configure
cd excel-to-sql-docs
npm install

# 4. Customize theme
# - Add logo
# - Configure colors (match GitHub repo)
# - Add navigation structure

# 5. Migrate content
# - Copy README sections to MDX files
# - Add metadata (title, description)
# - Organize into folders

# 6. Deploy
vercel add excel-to-sql-docs
# or
npm run build
```

### Configuration Files

**`fumadocs.config.ts`:**
```typescript
import { defineConfig } from 'fumadocs-docs/config'

export default defineConfig({
  title: 'excel-to-sql',
  description: 'Powerful CLI tool and Python SDK for importing Excel files into SQLite',
  // Add logo, URLs, etc.
})
```

**`app/layout.tsx`:**
- Add Google Analytics (optional)
- Configure theme colors
- Add font (Inter or similar)

## ✅ Acceptance Criteria

### Must Have (P0)
- [ ] Homepage with project introduction
- [ ] Getting Started guide (installation, quick start)
- [ ] CLI reference documentation
- [ ] Python SDK documentation
- [ ] Auto-Pilot Mode documentation
- [ ] Full-text search functionality
- [ ] Dark mode toggle
- [ ] Deployed to production (Vercel)
- [ ] Custom domain configured (docs.excel-to-sql.com or similar)

### Should Have (P1)
- [ ] API reference (auto-generated)
- [ ] Version selector (v0.3.0, v0.2.0)
- [ ] Interactive code examples with copy button
- [ ] Screenshots of CLI output
- [ ] Architecture diagrams
- [ ] Examples section with real datasets
- [ ] Changelog per version

### Could Have (P2)
- [ ] Algolia search (faster, better UX)
- [ ] On-page navigation (table of contents)
- [ ] Edit on GitHub link
- [ ] Disqus/Giscus comments
- [ ] RSS feed for updates
- [ ] PDF export of documentation

## 📊 Success Metrics

- **Time to find answer:** < 30 seconds (via search)
- **Page load time:** < 2 seconds (Lighthouse performance)
- **Mobile responsive:** Fully functional on mobile devices
- **SEO ranking:** Top 3 results for "excel to sqlite python"
- **User satisfaction:** Positive feedback on GitHub issues

## 🚀 Launch Plan

### Pre-Launch
1. Set up Fumadocs project locally
2. Migrate core content (Phase 1)
3. Test all navigation and links
4. Get feedback from 2-3 users

### Launch
1. Deploy to Vercel (staging)
2. Test staging environment thoroughly
3. Set up custom domain
4. Production deployment
5. Announce on GitHub README (add link to docs)
6. Post release notes

### Post-Launch
1. Monitor analytics (page views, search queries)
2. Gather user feedback
3. Iterate on content based on usage patterns
4. Keep in sync with new releases

## 🔗 Resources

- **Fumadocs Documentation:** https://fumadocs.vercel.app/
- **Fumadocs GitHub:** https://github.com/fuma-dev/fumadocs
- **Next.js Documentation:** https://nextjs.org/docs
- **MDX Documentation:** https://mdxjs.com/
- **Vercel Deployment:** https://vercel.com/docs

## 💬 Open Questions

1. **Domain Name:** Should we use `docs.excel-to-sql.com`, `excel-to-sql.dev/docs`, or a subdomain of existing site?
2. **Search Provider:** Use local search or Algolia? (Depends on content size)
3. **API Documentation:** Auto-generate from docstrings or manual?
4. **Analytics:** Add Google Analytics or privacy-focused alternative?
5. **Commenting:** Enable comments on doc pages? (Disqus, Giscus)

## 🤝 Contributing

Once the documentation website is set up:
- Community can contribute via PRs (like GitHub)
- Each MDX file can be edited independently
- Easy to add new examples and guides
- Version control for all changes

## 📅 Timeline Estimate

- **Setup & Configuration:** 4-6 hours
- **Content Migration (Phase 1):** 8-12 hours
- **Design & Customization:** 4-6 hours
- **Testing & Review:** 2-4 hours
- **Deployment & Domain Setup:** 1-2 hours

**Total:** 19-30 hours (3-4 days of focused work)

## 🔗 Related Issues

- Depends on: v0.3.0 release (completed)
- Blocks: v0.4.0 documentation updates
- Related: Better code documentation (docstrings)

---

**Note:** This issue should be implemented when the project reaches significant adoption (500+ PyPI downloads/month) or when the README becomes unwieldy to maintain. The current README is sufficient for early adopters.
