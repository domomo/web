module.exports = {
  testEnvironment: 'jsdom',
  transform: {
    '^.+\\.vue$': '@vue/vue3-jest',
    '^.+\\.[jt]s$': 'babel-jest',
  },
  moduleFileExtensions: ['js', 'json', 'vue'],
  testMatch: ['<rootDir>/src/**/*.test.js'],
};
