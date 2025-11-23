# Ensure the exported Next.js showcase (FinalProject) is copied verbatim into _site
# so the /FinalProject/_next assets are always present when running `jekyll build` or `jekyll serve`.
require "fileutils"

Jekyll::Hooks.register :site, :post_write do |site|
  src  = File.join(site.source, "FinalProject")
  dest = File.join(site.dest,   "FinalProject")

  next unless File.directory?(src)

  FileUtils.rm_rf(dest)
  FileUtils.mkdir_p(dest)
  # Copy everything, including dotfiles like .nojekyll
  FileUtils.cp_r(File.join(src, "."), dest)
end
