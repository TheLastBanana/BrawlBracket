// Include gulp
var gulp = require('gulp');

// Include plugins
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');
var gulpIf = require('gulp-if');
var useref = require('gulp-useref');
var imagemin = require('gulp-imagemin');
var cleanCSS = require('gulp-clean-css');
var rename = require('gulp-rename');
var cache = require('gulp-cache');
var sass = require('gulp-sass');
var babel = require('gulp-babel');
var del = require('del');
var merge = require('merge-stream');
var runSequence = require('run-sequence');
var browserSync = require('browser-sync');

// Remove dist
gulp.task('clean', function() {
    return del('brawlbracket/dist');
});

// Minify CSS
gulp.task('css', function() {
    // Exclude already minified files
    var minify = gulp.src(['brawlbracket/src/static/**/*.css', '!brawlbracket/src/static/**/*.min.css'])
        .pipe(cleanCSS())
        .pipe(rename({suffix: '.min'}))
        .pipe(gulp.dest('brawlbracket/dist/static/'));

    // Now copy minified files
    var copy = gulp.src('brawlbracket/src/static/**/*.min.css')
        .pipe(gulp.dest('brawlbracket/dist/static/'));

    var compSass = gulp.src('brawlbracket/src/static/**/*.scss')
        .pipe(sass().on('error', sass.logError))
        .pipe(cleanCSS())
        .pipe(rename({suffix: '.min'}))
        .pipe(gulp.dest('brawlbracket/dist/static/'));

    return merge(minify, copy, compSass);
});

// Just copy HTML
gulp.task('html', function() {
    return gulp.src('brawlbracket/src/templates/**/*.html')
        .pipe(gulp.dest('brawlbracket/dist/templates/'));
});

// Copy over existing .min.js files
gulp.task('copy-min-js', function() {
    return gulp.src('brawlbracket/src/static/**/*.min.js')
        .pipe(gulp.dest('brawlbracket/dist/static/'));
});

// Transpile JSX to JS
gulp.task('jsx', function() {
    return gulp.src('brawlbracket/src/static/**/*.jsx')
        .pipe(babel({'presets': ['react']}))
        .on('error', function(e) {
          console.log(e);
          this.emit('end');
        })
        .pipe(rename({
          extname: '.min.js'
        }))
        .pipe(gulp.dest('brawlbracket/dist/static/'));
});

// Just copy JavaScript files, but treat them as .min files so they can be included easily
gulp.task('rename-js', function() {
    return gulp.src(['brawlbracket/src/static/**/*.js', '!brawlbracket/src/static/**/*.min.js'])
        .pipe(rename({suffix: '.min'}))
        .pipe(gulp.dest('brawlbracket/dist/static/'));
});

// Set up JavaScript for development
gulp.task('js-dev', function(cb) {
    runSequence('copy-min-js', ['jsx', 'rename-js'], cb);
});

// Copy HTML files and combine + minify JS files
gulp.task('useref', function() {
    return gulp.src('brawlbracket/src/templates/**/*.html')

        // These files will end up in /templates/static. There's a 'base' option to send them elsewhere,
        // but when used, some files go missing for reasons unknown... so instead, we'll move them manually.
        .pipe(useref({
            searchPath: 'brawlbracket/src'
        }))

        // Minify JS files
        .pipe(gulpIf('*.js', uglify()))

        .pipe(gulp.dest('brawlbracket/dist/templates/'));
});

// Optimize images
gulp.task('img', function() {
    return gulp.src('brawlbracket/src/static/**/*.+(png|jpg|gif|svg)')
        .pipe(cache(imagemin()))
        .pipe(gulp.dest('brawlbracket/dist/static'));
});

// Copy sounds
gulp.task('sfx', function() {
    return gulp.src('brawlbracket/src/static/**/*.+(ogg|mp3)')
        .pipe(gulp.dest('brawlbracket/dist/static'));
});

// Copy fonts
gulp.task('fonts', function() {
    return gulp.src('brawlbracket/src/static/**/*.+(woff2|woff|ttf)')
        .pipe(gulp.dest('brawlbracket/dist/static'));
});

// Copy combined files from useref to the right place
gulp.task('useref-copy', function() {
    return gulp.src('brawlbracket/dist/templates/static/**/*')
        .pipe(gulp.dest('brawlbracket/dist/static'));
});

// Remove static files sitting in templates dir
gulp.task('useref-clean', function() {
    return del('brawlbracket/dist/templates/static');
});

// Clear the cache
gulp.task('clear-cache', function(cb) {
    return cache.clearAll(cb);
});

// Watch for file changes. Note that this doesn't minify anything, as this is aimed at dev mode, where we don't want to
// minify files for debugging reasons.
// This also causes browser-sync to reload when files change.
gulp.task('watch', function() {
    gulp.watch('brawlbracket/src/**/*.html', ['html', 'reload']);
    gulp.watch(['brawlbracket/src/**/*.js', 'brawlbracket/src/**/*.jsx'], ['js-dev', 'reload']);
    gulp.watch(['brawlbracket/src/**/*.css', 'brawlbracket/src/**/*.scss'], ['css', 'reload']);
    gulp.watch('brawlbracket/src/**/*.+(png|jpg|gif|svg)', ['img', 'reload']);
    gulp.watch('brawlbracket/src/**/*.+(mp3|ogg)', ['sfx', 'reload']);
    gulp.watch('brawlbracket/src/**/*.+(woff2|woff|ttf)', ['fonts', 'reload']);
});

// Start browser-sync server
gulp.task('browser-sync', function() {
    browserSync.init({
        proxy: 'localhost:5000',
        open: false
    });
});

// Reload browser-sync
gulp.task('reload', ['html', 'js-dev', 'css', 'img', 'sfx', 'fonts'], function() {
    console.log('Reloading browser');

    browserSync.reload();
});


// Combine all the tasks for deployment
gulp.task('all-deploy', function(cb) {
    runSequence('clean',
                ['css', 'js', 'useref', 'img', 'sfx', 'fonts'],
                'useref-copy',
                'useref-clean',
                cb);
});

// Combine all the tasks for development
gulp.task('all-dev', function(cb) {
    runSequence('clean',
                ['css', 'js-dev', 'html', 'img', 'sfx', 'fonts'],
                cb);
});

// Do a development run, then start the watcher and browser sync.
gulp.task('default', function(cb) {
    runSequence('all-dev', ['watch', 'browser-sync'], cb);
});
