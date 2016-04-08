// Include gulp
var gulp = require('gulp');

// Include plugins
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');
var useref = require('gulp-useref');
var gulpIf = require('gulp-if');
var imagemin = require('gulp-imagemin');
var cleanCSS = require('gulp-clean-css');
var rename = require('gulp-rename');
var cache = require('gulp-cache');
var sass = require('gulp-sass');
var babel = require('gulp-babel');
var util = require('gulp-util');
var mode = require('gulp-mode')();
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
        .pipe(cleanCSS({processImport: false}))
        .pipe(rename({suffix: '.min'}))
        .pipe(gulp.dest('brawlbracket/dist/static/'));

    // Now copy minified files
    var copy = gulp.src('brawlbracket/src/static/**/*.min.css')
        .pipe(gulp.dest('brawlbracket/dist/static/'));

    var compSass = gulp.src('brawlbracket/src/static/**/*.scss')
        .pipe(sass().on('error', sass.logError))
        .pipe(cleanCSS({processImport: false}))
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
        .pipe(mode.production(uglify()))
        .pipe(rename({
          extname: '.min.js'
        }))
        .pipe(gulp.dest('brawlbracket/dist/static/'));
});

// Rename .js files to .min.js, and in production mode, actually minify brawlbracket files
gulp.task('minify-js', function() {
    var pattern = ['!brawlbracket/src/static/brawlbracket/**/*'];
    
    // In production mode, we want actual minified files. In development, just rename them
    if (util.env.production) {
        pattern += ['brawlbracket/src/static/**/*.min.js'];
    } else {
        pattern += ['brawlbracket/src/static/**/*.js', '!**/*.min.js'];
    }
    
    // Outside libraries. Separated because we never minify these.
    var libs = gulp.src(pattern)
        .pipe(rename({suffix: '.min'}))
        .pipe(gulp.dest('brawlbracket/dist/static/'));
    
    // BrawlBracket source hasn't been minified yet, so it needs to be handled differently
    var source = gulp.src(['brawlbracket/src/static/brawlbracket/**/*.js'])
        .pipe(mode.production(gulpIf('*.js', uglify())))
        .pipe(rename({suffix: '.min'}))
        .pipe(gulp.dest('brawlbracket/dist/static/brawlbracket/'));
        
    return merge(libs, source);
});

// Set up JavaScript for development
gulp.task('js', function(cb) {
    runSequence('copy-min-js', ['jsx', 'minify-js'], cb);
});

// Run all the parts of the useref task
gulp.task('useref', function(cb) {
    runSequence(
        'useref-parse',
        'useref-copy',
        'useref-clean',
        cb
    );
});

// Copy HTML files and combine + minify included JS files
gulp.task('useref-parse', function() {
    return gulp.src('brawlbracket/src/templates/**/*.html')

        // These files will end up in /templates/static. There's a 'base' option to send them elsewhere,
        // but when used, some files go missing for reasons unknown... so instead, we'll move them manually.
        .pipe(useref({
            searchPath: 'brawlbracket/dist'
        }))
        .on('error', function(e) {
          console.log(e);
          this.emit('end');
        })

        .pipe(gulp.dest('brawlbracket/dist/templates/'));
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

// Optimize images
gulp.task('img', function() {
    return gulp.src('brawlbracket/src/static/**/*.+(png|jpg|gif|svg)')
//        .pipe(cache(imagemin()))
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

// Clear the cache
gulp.task('clear-cache', function(cb) {
    return cache.clearAll(cb);
});

// Watch for file changes. Note that this doesn't minify anything, as this is aimed at dev mode, where we don't want to
// minify files for debugging reasons.
// This also causes browser-sync to reload when files change.
gulp.task('watch', function() {
    gulp.watch('brawlbracket/src/**/*.html', ['html', 'reload']);
    gulp.watch(['brawlbracket/src/**/*.js', 'brawlbracket/src/**/*.jsx'], ['js', 'reload']);
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
gulp.task('reload', ['html', 'js', 'css', 'img', 'sfx', 'fonts', 'useref'], function() {
    console.log('Reloading browser');

    browserSync.reload();
});


// Combine all the tasks for deployment
gulp.task('deploy', function(cb) {
    if (util.env.production) {
        runSequence(
            'clean',
            ['css', 'js', 'img', 'sfx', 'fonts'],
            'useref',
            cb
        );
        
    } else {
        runSequence(
            'clean',
            ['css', 'js', 'img', 'sfx', 'fonts'],
            'html',
            cb
        );
    }
});

// Do a development run, then start the watcher and browser sync.
gulp.task('default', function(cb) {
    runSequence('deploy', ['watch', 'browser-sync'], cb);
});
