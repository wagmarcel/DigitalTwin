// test/common.test.js

const chai = require('chai');
const sinon = require('sinon');
const expect = chai.expect;
const proxyquire = require('proxyquire');
const path = require('path'); // Ensure path is required

chai.use(require('sinon-chai'));

describe('common', function () {
  let fsStub;
  let pathStub;
  let configStub;
  let loggerStub;
  let common;
  let commonPath; // Variable to store the path of common.js

  beforeEach(function () {
    // Create stubs for fs methods
    fsStub = {
      writeFileSync: sinon.stub(),
      readFileSync: sinon.stub(),
      existsSync: sinon.stub(),
      mkdirSync: sinon.stub(),
    };

    // Create stubs for path methods
    pathStub = {
      resolve: sinon.stub(),
      normalize: sinon.stub(),
      join: sinon.stub(),
    };

    // Stub the config module
    configStub = {
      data_directory: '/data',
      getConfigName: sinon.stub().returns('/config/config.json'),
    };

    // Stub the logger
    loggerStub = {
      info: sinon.stub(),
      error: sinon.stub(),
      debug: sinon.stub(),
    };

    // Determine the directory of common.js
    commonPath = path.dirname(require.resolve('../lib/common'));

    // Use proxyquire to inject stubs
    common = proxyquire('../lib/common', {
      fs: fsStub,
      path: pathStub,
      '../config': configStub,
      './logger': {
        init: () => loggerStub,
      },
    });

    // Initialize the logger
    common.init(loggerStub);

    // Default behaviors
    pathStub.resolve.callsFake((...args) => args.join('/'));
    pathStub.normalize.callsFake((p) => p);
    fsStub.existsSync.returns(true);
    fsStub.readFileSync.returns('{}');
  });

  afterEach(function () {
    sinon.restore();
  });

  describe('writeToJson', function () {
    it('should write data to a JSON file successfully', function () {
      fsStub.writeFileSync.returns(null);

      const result = common.writeToJson('test.json', { key: 'value' });

      expect(fsStub.writeFileSync).to.have.been.calledWith(
        'test.json',
        JSON.stringify({ key: 'value' }, null, 4)
      );
      expect(loggerStub.info).to.have.been.calledWith('Object data saved to test.json');
      expect(result).to.be.false;
    });

    it('should log an error if writing fails', function () {
      const error = new Error('Write failed');
      fsStub.writeFileSync.throws(error);

      const result = common.writeToJson('test.json', { key: 'value' });

      expect(loggerStub.error).to.have.been.calledWith('The file could not be written ', error);
      expect(result).to.be.true;
    });
  });

  describe('readFileToJson', function () {
    it('should read and parse JSON from a file', function () {
      fsStub.existsSync.returns(true);
      fsStub.readFileSync.returns('{"key":"value"}');

      const result = common.readFileToJson('test.json');

      expect(fsStub.readFileSync).to.have.been.calledWith('test.json');
      expect(result).to.deep.equal({ key: 'value' });
      expect(loggerStub.debug).to.have.been.calledWith(
        'Filename: test.json Contents:',
        { key: 'value' }
      );
    });

    it('should log an error if JSON parsing fails', function () {
      fsStub.existsSync.returns(true);
      fsStub.readFileSync.returns('Invalid JSON');

      const result = common.readFileToJson('test.json');

      expect(loggerStub.error).to.have.been.calledWith(
        'Improper JSON format:',
        sinon.match.string
      );
      expect(result).to.be.null;
    });

    it('should return null if file does not exist', function () {
      fsStub.existsSync.returns(false);

      const result = common.readFileToJson('test.json');

      expect(result).to.be.null;
    });
  });

  describe('initializeDataDirectory', function () {
    it('should create data directory if it does not exist', function () {
      fsStub.existsSync.returns(false);

      common.initializeDataDirectory();

      expect(fsStub.mkdirSync).to.have.been.calledWith('/data');
      expect(configStub.data_directory).to.equal('/data');
    });

    it('should not create data directory if it exists', function () {
      fsStub.existsSync.returns(true);

      common.initializeDataDirectory();

      expect(fsStub.mkdirSync).to.not.have.been.called;
    });
  });

  describe('initializeFile', function () {
    it('should create the file with data if it does not exist', function () {
      fsStub.existsSync.returns(false);
      sinon.stub(common, 'writeToJson');

      common.initializeFile('test.json', { key: 'value' });

      expect(common.writeToJson).to.have.been.calledWith('test.json', { key: 'value' });
    });

    it('should not create the file if it exists', function () {
      fsStub.existsSync.returns(true);
      sinon.stub(common, 'writeToJson');

      common.initializeFile('test.json', { key: 'value' });

      expect(common.writeToJson).to.not.have.been.called;
    });
  });

  describe('isAbsolutePath', function () {
    it('should return true for absolute paths', function () {
      pathStub.resolve.returns('/absolute/path');
      pathStub.normalize.returns('/absolute/path');

      const result = common.isAbsolutePath('/absolute/path');

      expect(result).to.be.true;
    });

    it('should return false for relative paths', function () {
      pathStub.resolve.returns('/resolved/relative/path');
      pathStub.normalize.returns('relative/path');

      const result = common.isAbsolutePath('relative/path');

      expect(result).to.be.false;
    });
  });

  describe('getFileFromDataDirectory', function () {
    it('should return the full path to the file in data directory (absolute path)', function () {
      configStub.data_directory = '/data';
      sinon.stub(common, 'isAbsolutePath').returns(true);
      pathStub.resolve.resetHistory();
      pathStub.resolve.withArgs('/data', 'test.json').returns('/data/test.json');

      const result = common.getFileFromDataDirectory('test.json');

      expect(pathStub.resolve).to.have.been.calledOnceWith('/data', 'test.json');
      expect(result).to.equal('/data/test.json');
    });

    it('should return the full path to the file in data directory (relative path)', function () {
      configStub.data_directory = 'data';
      sinon.stub(common, 'isAbsolutePath').returns(false);
      pathStub.resolve.resetHistory();

      // Use commonPath instead of __dirname
      pathStub.resolve
        .withArgs(commonPath, '..', 'data', 'test.json')
        .returns('/full/path/test.json');

      const result = common.getFileFromDataDirectory('test.json');

      expect(pathStub.resolve).to.have.been.calledOnceWith(commonPath, '..', 'data', 'test.json');
      expect(result).to.equal('/full/path/test.json');
    });
  });

  describe('getDeviceConfigName', function () {
    it('should return the device config filename', function () {
      sinon.stub(common, 'getFileFromDataDirectory').returns('device.json');
      fsStub.existsSync.returns(true);

      const result = common.getDeviceConfigName();

      expect(result).to.equal('device.json');
    });

    it('should initialize device config if it does not exist', function () {
      sinon.stub(common, 'getFileFromDataDirectory').returns('device.json');
      sinon.stub(common, 'initializeDeviceConfig');
      fsStub.existsSync.onFirstCall().returns(false).onSecondCall().returns(true);

      const result = common.getDeviceConfigName();

      expect(common.initializeDeviceConfig).to.have.been.called;
      expect(result).to.equal('device.json');
    });

    it('should exit the process if device config cannot be found', function () {
      sinon.stub(common, 'getFileFromDataDirectory').returns('device.json');
      sinon.stub(common, 'initializeDeviceConfig');
      fsStub.existsSync.returns(false);
      sinon.stub(process, 'exit');

      common.getDeviceConfigName();

      expect(loggerStub.error).to.have.been.calledWith('Failed to find device config file!');
      expect(process.exit).to.have.been.calledWith(0);
    });
  });

  describe('getDeviceConfig', function () {
    it('should return the device configuration', function () {
      sinon.stub(common, 'getDeviceConfigName').returns('device.json');
      sinon.stub(common, 'readFileToJson').returns({ device_id: '12345' });

      const result = common.getDeviceConfig();

      expect(result).to.deep.equal({ device_id: '12345' });
    });
  });

  describe('saveToDeviceConfig', function () {
    it('should save a key-value pair to the device config', function () {
      sinon.stub(common, 'getDeviceConfigName').returns('device.json');
      sinon.stub(common, 'saveConfig');

      common.saveToDeviceConfig('key', 'value');

      expect(common.saveConfig).to.have.been.calledWith('device.json', 'key', 'value');
    });
  });

  describe('buildPath', function () {
    it('should replace placeholders with data (single value)', function () {
      const result = common.buildPath('/api/{id}/data', '123');

      expect(result).to.equal('/api/123/data');
    });

    it('should replace placeholders with data (multiple values)', function () {
      const result = common.buildPath('/api/{id}/{type}', ['123', 'sensor']);

      expect(result).to.equal('/api/123/sensor');
    });
  });

  describe('isBinary', function () {
    it('should return true if object contains a Buffer', function () {
      const obj = {
        data: Buffer.from('test'),
      };

      const result = common.isBinary(obj);

      expect(result).to.be.true;
    });

    it('should return true if nested object contains a Buffer', function () {
      const obj = {
        data: {
          nested: Buffer.from('test'),
        },
      };

      const result = common.isBinary(obj);

      expect(result).to.be.true;
    });

    it('should return false if object does not contain a Buffer', function () {
      const obj = {
        data: 'test',
      };

      const result = common.isBinary(obj);

      expect(result).to.be.false;
    });
  });
});
