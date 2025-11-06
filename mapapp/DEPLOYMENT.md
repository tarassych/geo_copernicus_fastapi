# Deployment Guide

The map application has been built as a **static site** ready for deployment.

## 📦 Build Output

- **Location**: `out/` directory
- **Size**: ~1.5 MB
- **Type**: Static HTML/CSS/JS files
- **Requirements**: Any static web server or CDN

## 🚀 Deployment Options

### Option 1: Netlify (Recommended)

#### Via Netlify Drop (Easiest)
1. Go to https://app.netlify.com/drop
2. Drag and drop the `out/` folder
3. Done! Your site is live

#### Via Netlify CLI
```bash
npm install -g netlify-cli
cd out
netlify deploy --prod
```

### Option 2: Vercel

```bash
npm install -g vercel
cd out
vercel --prod
```

### Option 3: GitHub Pages

1. Create a new repository on GitHub
2. Add the contents of `out/` to the repository:
   ```bash
   cd out
   git init
   git add .
   git commit -m "Deploy map application"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```
3. In GitHub repository settings:
   - Go to Settings → Pages
   - Source: Deploy from a branch
   - Branch: main / (root)
   - Save

Your site will be available at: `https://YOUR_USERNAME.github.io/YOUR_REPO/`

### Option 4: AWS S3 + CloudFront

```bash
# Install AWS CLI
aws s3 sync out/ s3://your-bucket-name/ --delete

# Configure CloudFront to point to your S3 bucket
```

### Option 5: Google Cloud Storage

```bash
# Install Google Cloud SDK
gsutil -m rsync -r out/ gs://your-bucket-name/

# Make bucket public
gsutil iam ch allUsers:objectViewer gs://your-bucket-name
```

### Option 6: Any Static Web Server

Upload the contents of the `out/` directory to any web server:
- Apache
- Nginx
- IIS
- Python's SimpleHTTPServer
- Node.js http-server

Example with Node.js:
```bash
npx serve out
```

## 📁 What's in the `out/` Directory?

```
out/
├── index.html          # Main page
├── _next/             # Next.js assets (JS, CSS)
├── favicon.ico        # Favicon
├── 404.html           # 404 error page
└── *.svg, *.txt       # Other static assets
```

## 🔧 Configuration

### Custom Domain
After deploying, configure your custom domain in your hosting provider's settings.

### HTTPS
Most modern hosting providers (Netlify, Vercel, GitHub Pages) provide automatic HTTPS.

### Caching Headers (Optional)
For better performance, configure your CDN/server with these headers:

```
# For _next/static/* files (immutable)
Cache-Control: public, max-age=31536000, immutable

# For HTML files
Cache-Control: public, max-age=0, must-revalidate

# For other assets
Cache-Control: public, max-age=3600
```

## ✅ Deployment Checklist

- [x] Application built successfully (`npm run build`)
- [x] Static files generated in `out/` directory
- [x] Files are ~1.5 MB total
- [ ] Choose hosting provider
- [ ] Deploy `out/` directory
- [ ] Test deployed site
- [ ] (Optional) Configure custom domain
- [ ] (Optional) Set up CI/CD for automatic deployments

## 🌐 Test Deployment Locally

Before deploying, test the static build locally:

```bash
cd mapapp
npx serve out
```

Then open http://localhost:3000 in your browser.

## 📊 Application Features

The deployed application includes:
- Interactive Leaflet map
- 97 cached DEM tile boundaries
- Tile name labels
- DEM coverage visualization
- Map legend with statistics
- Responsive design
- No backend required
- No API keys needed

## 🔄 Updating the Application

To update the deployed site:

1. Make changes to the source code
2. Rebuild: `npm run build`
3. Redeploy the `out/` directory using your chosen method

## 📝 Notes

- The application is **100% static** - no server-side processing needed
- Works offline after initial load (PWA-ready if you add a service worker)
- Uses OpenStreetMap tiles (free, no API key required)
- Includes all necessary assets (no external dependencies except OSM tiles)
- Mobile-friendly and responsive

## 🆘 Troubleshooting

**Map not loading?**
- Check browser console for errors
- Ensure you're serving from a web server (not `file://`)
- Verify all files from `out/` are uploaded

**Tiles not showing?**
- Check `data/cached-tiles.json` is included
- Verify browser has internet access for OSM tiles

**404 errors on routes?**
- This is a single-page app - all routes should serve `index.html`
- Configure your hosting provider accordingly

## 📞 Support

For issues or questions, check:
- Next.js deployment docs: https://nextjs.org/docs/deployment
- Leaflet documentation: https://leafletjs.com/
- OpenStreetMap tile usage: https://wiki.openstreetmap.org/wiki/Tile_usage_policy

