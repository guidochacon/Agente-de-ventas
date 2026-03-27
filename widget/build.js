const esbuild = require('esbuild');
const path = require('path');

const isWatch = process.argv.includes('--watch');

const options = {
  entryPoints: [path.join(__dirname, 'src/widget.js')],
  bundle: true,
  minify: !isWatch,
  sourcemap: true,
  outfile: path.join(__dirname, 'dist/sales-agent-widget.min.js'),
  logLevel: 'info',
};

if (isWatch) {
  esbuild.context(options).then(ctx => ctx.watch());
} else {
  esbuild.build(options).catch(() => process.exit(1));
}
