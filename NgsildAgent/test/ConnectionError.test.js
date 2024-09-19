// test/ConnectionError.test.js

const chai = require('chai');
const expect = chai.expect;

// Import the ConnectionError class
const ConnectionError = require('../lib/ConnectionError');

describe('ConnectionError', function () {
  it('should create an error with errno 0 (Connection Reset)', function () {
    const errorMessage = 'Connection reset by peer';
    const error = new ConnectionError(0, errorMessage);

    expect(error).to.be.instanceOf(Error);
    expect(error).to.be.instanceOf(ConnectionError);
    expect(error.name).to.equal('ConnectionError');
    expect(error.errno).to.equal(0);
    expect(error.message).to.equal(errorMessage);
  });

  it('should create an error with errno 1 (Authorization Error)', function () {
    const errorMessage = 'Invalid credentials';
    const error = new ConnectionError(1, errorMessage);

    expect(error).to.be.instanceOf(Error);
    expect(error).to.be.instanceOf(ConnectionError);
    expect(error.name).to.equal('ConnectionError');
    expect(error.errno).to.equal(1);
    expect(error.message).to.equal(errorMessage);
  });

  it('should create an error with errno 2 (Other)', function () {
    const errorMessage = 'Unknown error occurred';
    const error = new ConnectionError(2, errorMessage);

    expect(error).to.be.instanceOf(Error);
    expect(error).to.be.instanceOf(ConnectionError);
    expect(error.name).to.equal('ConnectionError');
    expect(error.errno).to.equal(2);
    expect(error.message).to.equal(errorMessage);
  });

  it('should create an error with a custom errno and message', function () {
    const customErrno = 99;
    const errorMessage = 'Custom error';
    const error = new ConnectionError(customErrno, errorMessage);

    expect(error).to.be.instanceOf(Error);
    expect(error).to.be.instanceOf(ConnectionError);
    expect(error.name).to.equal('ConnectionError');
    expect(error.errno).to.equal(customErrno);
    expect(error.message).to.equal(errorMessage);
  });

  it('should have a stack trace', function () {
    const error = new ConnectionError(0, 'Error with stack trace');

    expect(error.stack).to.be.a('string');
    expect(error.stack).to.include('ConnectionError');
  });
});
