'use strict';

module.exports = function ( grunt ) {
    grunt.util.linefeed = '\n';

    grunt.initConfig({
        clean: {
            images: {
                src: [
                    'web/static/images/*.png',
                    'web/static/images/*.gif',
                    'web/static/images/*.jpg',                                        
                ]
            }
        },
        // concat multiple js files together
        concat: {
            all: {
                src: [
                    'web/static/js/jquery-1.10.2.js',
                    'web/static/js/underscore.js',                    
                    'web/static/js/backbone.js',












                    'web/bootstrap/js/scaffolding.js'
                ],
                dest: 'web/static/js/javascript.js',
            },  
            bootstrap: {
                src: [
                    'web/bootstrap/js/transition.js',
                    'web/bootstrap/js/alert.js',
                    'web/bootstrap/js/button.js',
                    'web/bootstrap/js/carousel.js',
                    'web/bootstrap/js/collapse.js',
                    'web/bootstrap/js/dropdown.js',
                    'web/bootstrap/js/modal.js',
                    'web/bootstrap/js/tooltip.js',
                    'web/bootstrap/js/popover.js',
                    'web/bootstrap/js/scrollspy.js',
                    'web/bootstrap/js/tab.js',
                    'web/bootstrap/js/affix.js'
                ],
                dest: 'web/static/js/javascript.js'
            }    
        },

        // js code checker
        jshint: {
            options: {
                jshintrc: 'web/bootstrap/js/.jshintrc'
            },
            src: {
                src: 'web/static/js/javascript.js'
            },
        },

        uglify: {
            all: {
                src: 'web/static/js/javascript.js',
                dest: 'web/static/js/javascript.min.js'
            }
        },

        // start of image tasks
        sketch_export: {
            all: {
                options: {
                    type: 'slices',
                    scales: [
                        1.0,
                        2.0
                    ],
                    overwrite: true,
                    saveForWeb: true,
                    formats: [
                        'png',
                        'jpg'
                    ]
                },
                //expand: true,
                //cwd: 'design/web/design/',
                //src: ['*.sketch'],
                src: 'design/web/design/bootstrap.sketch',
                dest: 'web/static/images/'
            },
            icons: {
                options: {
                    type: 'slices',
                    scales: [
                        1.0,
                        2.0
                    ],
                    overwrite: true,
                    saveForWeb: true,
                    formats: [
                        'png',
                        'jpg'
                    ]
                },
                src: 'design/web/design/icons.sketch',
                dest: 'web/static/images/'
            }
        },

        imagemin: {
            all: {
                files: [{
                    expand: true,
                    cwd: 'web/static/images',
                    src: '*.{gif,GIF,jpg,JPG,png,PNG}',
                    dest: 'web/static/images'
                }]
            }
        },

        less: {
            compileCore: {
                options: {
                    strictMath: true,
                    sourceMap: true,
                    outputSourceFiles: true,
                    sourceMapURL: 'bootstrap.css.map',
                    sourceMapFilename: 'web/static/css/style.css.map'
                },
                files: {
                    'web/static/css/style.css': 'web/bootstrap/less/bootstrap.less'
                }
            },
            minify: {
                options: {
                    cleancss: true
                },
                files: {
                    'web/static/css/style.min.css': 'web/static/css/style.css',
                }
            }
        },

        // add in all -webkit- prefixes, etc
        autoprefixer: {
            options: {
                browsers: ['last 2 versions', 'ie 8', 'ie 9', 'android 2.3', 'android 4', 'opera 12']
            },
            core: {
                options: {
                map: true
                },
                src: 'web/static/css/style.css'
            },
        },

        // fix order of css entries
        csscomb: {
            options: {
                config: 'web/bootstrap/less/.csscomb.json'
            },
            dist: {
                expand: true,
                cwd: 'web/static/css/',
                src: ['*.css', '!*.min.css'],
                dest: 'web/static/css/'
            },
        },

        // check for css errors
        csslint: {
            options: {
                csslintrc: 'web/bootstrap/less/.csslintrc'
            },
            src: [
                'web/static/css/style.css'
            ],
        },

        watch: {
            images: {
                files: 'design/web/design/bootstrap.sketch',
                tasks: ['sketch']
            },
            icons: {
                files: 'design/web/design/icons.sketch',
                tasks: ['sketch']
            },
            js: {
                files: 'web/bootstrap/js/*.js',
                tasks: ['dist-js']
            },
            css: {
                files: 'web/bootstrap/less/*.less',
                tasks: 'dist-css'
            }
        },
	});

    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-newer');
    grunt.loadNpmTasks('grunt-contrib-less');
    grunt.loadNpmTasks('grunt-contrib-imagemin');
    grunt.loadNpmTasks('grunt-sketch');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-autoprefixer');
    grunt.loadNpmTasks('grunt-csscomb');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-contrib-csslint');
    grunt.loadNpmTasks('grunt-contrib-clean');

    // js tasks
    grunt.registerTask('concatjs', ['concat:all']);
    grunt.registerTask('uglifyjs', ['uglify:all']);
    grunt.registerTask('jshintjs', ['jshint']);
    grunt.registerTask('dist-js', ['concat:all', 'uglify:all', ]);        

    // css tasks
    grunt.registerTask('less-compile', ['less:compileCore', 'less:minify']);
    grunt.registerTask('css-lint', ['csslint']);
    grunt.registerTask('dist-css', ['less-compile', 'autoprefixer', 'csscomb', 'less:minify']);    

    // images tasks
    grunt.registerTask('sketch', [ 'newer:clean:images', 'sketch_export:all', 'sketch_export:icons' ] );
    grunt.registerTask('image-min', [ 'newer:imagemin:all' ] );
    grunt.registerTask('dist-images', [ 'clean:images', 'sketch', 'image-min' ] );    

    grunt.registerTask( 'default', [ 'dist-images', 'dist-css', 'dist-js'] );
};