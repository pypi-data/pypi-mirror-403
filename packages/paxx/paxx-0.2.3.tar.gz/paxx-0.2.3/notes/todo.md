fix next steps in /Users/adam/Coding/facet/.venv/bin/paxx deploy add linux-server

Linux-server deployment added!

Next steps:
  1. Copy deploy/linux-server/.env.example, rename to deploy/linux-server/.env and customize it.
  2. Push to GitHub the changes you want to deploy.
  3. Create a git tag to trigger the build, eg.: git tag v1.0.0 && git push origin v1.0.0
  4. Run: ./deploy/linux-server/deploy-init.sh user@your-server