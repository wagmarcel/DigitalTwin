// test/ConnectionManager.test.js

const chai = require('chai');
const sinon = require('sinon');
const expect = chai.expect;
const proxyquire = require('proxyquire');

chai.use(require('sinon-chai'));

describe('ConnectionManager', function () {
  let mqttStub;
  let mqttClientStub;
  let ConnectionManager;
  let connectionManager;
  let loggerStub;
  let ConnectionError;
  let conf;

  beforeEach(function () {
    // Stub the mqtt client methods
    mqttClientStub = {
      endAsync: sinon.stub().resolves(),
      publishAsync: sinon.stub().resolves(),
      on: sinon.stub(),
      connected: true,
    };

    // Stub the mqtt module
    mqttStub = {
      connectAsync: sinon.stub().resolves(mqttClientStub),
    };

    // Stub the logger
    loggerStub = {
      info: sinon.stub(),
      error: sinon.stub(),
      debug: sinon.stub(),
    };

    // Require the ConnectionError class
    ConnectionError = require('../lib/ConnectionError');

    // Proxyquire ConnectionManager to inject mqttStub
    ConnectionManager = proxyquire('../lib/ConnectionManager', {
      mqtt: mqttStub,
    });

    // Configuration object
    conf = {
      host: 'localhost',
      port: 1883,
      websockets: false,
      secure: false,
      keepalive: 60,
      retries: 30,
      qos: 1,
      retain: false,
    };

    // Instantiate ConnectionManager
    connectionManager = new ConnectionManager(conf, loggerStub);
  });

  afterEach(function () {
    sinon.restore();
  });

  describe('constructor', function () {
    it('should initialize with the correct configuration', function () {
      expect(connectionManager.host).to.equal('localhost');
      expect(connectionManager.port).to.equal(1883);
      expect(connectionManager.websockets).to.be.false;
      expect(connectionManager.secure).to.be.false;
      expect(connectionManager.keepalive).to.equal(60);
      expect(connectionManager.max_retries).to.equal(30);
      expect(connectionManager.pubArgs).to.deep.equal({ qos: 1, retain: false });
      expect(connectionManager.isLive).to.be.false;
      expect(connectionManager.deviceInfo).to.deep.equal({});
      expect(connectionManager.logger).to.equal(loggerStub);
      expect(connectionManager.authorized).to.be.false;
    });
  });

  describe('init', function () {
    it('should initialize MQTT client with correct URL and options', async function () {
      connectionManager.deviceInfo = {
        device_id: 'device123',
        device_token: 'token123',
      };

      await connectionManager.init();

      const expectedUrl = 'mqtt://localhost:1883';
      expect(mqttStub.connectAsync).to.have.been.calledWith(expectedUrl, {
        username: 'device123',
        password: 'token123',
        rejectUnauthorized: false,
      });
      expect(connectionManager.client).to.equal(mqttClientStub);

      // Verify event handlers are set
      expect(mqttClientStub.on.callCount).to.equal(5);
      expect(mqttClientStub.on).to.have.been.calledWith('connect', sinon.match.func);
      expect(mqttClientStub.on).to.have.been.calledWith('reconnect', sinon.match.func);
      expect(mqttClientStub.on).to.have.been.calledWith('offline', sinon.match.func);
      expect(mqttClientStub.on).to.have.been.calledWith('error', sinon.match.func);
      expect(mqttClientStub.on).to.have.been.calledWith('end', sinon.match.func);

      expect(connectionManager.authorized).to.be.true;
    });

    it('should handle secure MQTT connections', async function () {
      conf.secure = true;
      connectionManager = new ConnectionManager(conf, loggerStub);
      connectionManager.deviceInfo = {
        device_id: 'device123',
        device_token: 'token123',
      };

      await connectionManager.init();

      const expectedUrl = 'mqtts://localhost:1883';
      expect(mqttStub.connectAsync).to.have.been.calledWith(expectedUrl, sinon.match.object);
    });

    it('should handle WebSocket connections', async function () {
      conf.websockets = true;
      connectionManager = new ConnectionManager(conf, loggerStub);
      connectionManager.deviceInfo = {
        device_id: 'device123',
        device_token: 'token123',
      };

      await connectionManager.init();

      const expectedUrl = 'ws://localhost:1883';
      expect(mqttStub.connectAsync).to.have.been.calledWith(expectedUrl, sinon.match.object);
    });

    it('should handle secure WebSocket connections', async function () {
      conf.websockets = true;
      conf.secure = true;
      connectionManager = new ConnectionManager(conf, loggerStub);
      connectionManager.deviceInfo = {
        device_id: 'device123',
        device_token: 'token123',
      };

      await connectionManager.init();

      const expectedUrl = 'wss://localhost:1883';
      expect(mqttStub.connectAsync).to.have.been.calledWith(expectedUrl, sinon.match.object);
    });

    it('should handle errors during MQTT connection', async function () {
      const error = new Error('Connection failed');
      mqttStub.connectAsync.rejects(error);
      sinon.stub(connectionManager, 'createConnectionError').returns(new ConnectionError(0, 'Connection failed'));

      try {
        await connectionManager.init();
        expect.fail('Expected init to throw an error');
      } catch (err) {
        expect(connectionManager.createConnectionError).to.have.been.calledWith(error);
        expect(err).to.be.instanceOf(ConnectionError);
        expect(err.message).to.equal('Connection failed');
      }
    });

    it('should call client.endAsync if client already exists', async function () {
      connectionManager.client = mqttClientStub;
      mqttClientStub.endAsync.resolves();

      connectionManager.deviceInfo = {
        device_id: 'device123',
        device_token: 'token123',
      };

      await connectionManager.init();

      expect(mqttClientStub.endAsync).to.have.been.calledOnce;
      expect(mqttStub.connectAsync).to.have.been.calledOnce;
    });
  });

  describe('publish', function () {
    it('should publish a message to a topic', async function () {
      connectionManager.client = mqttClientStub;

      const topic = 'test/topic';
      const message = { key: 'value' };
      const options = { qos: 1, retain: false };

      await connectionManager.publish(topic, message, options);

      expect(mqttClientStub.publishAsync).to.have.been.calledWith(
        topic,
        JSON.stringify(message),
        options
      );
    });
  });

  describe('connected', function () {
    it('should return true when client is connected', function () {
      connectionManager.client = mqttClientStub;
      mqttClientStub.connected = true;

      const result = connectionManager.connected();

      expect(result).to.be.true;
    });

    it('should return false when client is not connected', function () {
      connectionManager.client = mqttClientStub;
      mqttClientStub.connected = false;

      const result = connectionManager.connected();

      expect(result).to.be.false;
    });

    it('should return false when client is undefined', function () {
      connectionManager.client = undefined;

      const result = connectionManager.connected();

      expect(result).to.be.false;
    });
  });

  describe('authorized', function () {
    it('should return true when authorized is true', function () {
      connectionManager.authorized = true;

      const result = connectionManager.isAuthorized();

      expect(result).to.be.true;
    });

    it('should return false when authorized is false', function () {
      connectionManager.authorized = false;

      const result = connectionManager.isAuthorized();

      expect(result).to.be.false;
    });
  });

  describe('createConnectionError', function () {
    it('should return ConnectionError with errno 0 when err.errno === -111', function () {
      const error = { errno: -111, message: 'Connection refused' };

      const result = connectionManager.createConnectionError(error);

      expect(result).to.be.instanceOf(ConnectionError);
      expect(result.errno).to.equal(0);
      expect(result.message).to.equal('Connection refused');
    });

    it('should return ConnectionError with errno 1 when err.code === 5', function () {
      const error = { code: 5, message: 'Authorization failed' };

      const result = connectionManager.createConnectionError(error);

      expect(result).to.be.instanceOf(ConnectionError);
      expect(result.errno).to.equal(1);
      expect(result.message).to.equal('Authorization failed');
    });

    it('should return the original error when no matching errno or code', function () {
      const error = new Error('Unknown error');

      const result = connectionManager.createConnectionError(error);

      expect(result).to.equal(error);
    });
  });

  describe('updateDeviceInfo', function () {
    it('should update deviceInfo property', function () {
      const deviceInfo = { device_id: 'device123', device_token: 'token123' };

      connectionManager.updateDeviceInfo(deviceInfo);

      expect(connectionManager.deviceInfo).to.deep.equal(deviceInfo);
    });
  });
});
