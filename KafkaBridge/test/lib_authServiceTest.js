/* eslint-disable no-useless-constructor */
/**
* Copyright (c) 2021 Intel Corporation
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*    http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/

const assert = require('chai').assert;
const rewire = require('rewire');
const chai = require('chai');
global.should = chai.should();

let fileToTest = '../lib/authService/authenticate.js';

const PUBLISH = '2';

describe(fileToTest, function () {
  const ToTest = rewire(fileToTest);
  class Logger {
    info () {}
    debug () {}
  };
  class Cache {};
  ToTest.__set__('Logger', Logger);
  ToTest.__set__('Cache', Cache);
  it('Shall verify and decode token successfully', function (done) {
    const decodedToken = { sub: '1234' };
    const config = {};
    const Authenticate = ToTest.__get__('Authenticate');
    const auth = new Authenticate(config);
    auth.keycloakAdapter = {
      grantManager: {
        createGrant: () => {
          return Promise.resolve({
            access_token: {
              content: decodedToken
            }
          });
        }
      }
    };
    auth.verifyAndDecodeToken('ex1123').then(result => {
      assert.equal(decodedToken, result, 'Wrong decoded Token');
      done();
    }).catch(err => {
      done(err);
    });
  });
  it('Shall verify and decode token unsuccessfully', function (done) {
    const message = 'No valid token';
    const config = {};
    const Authenticate = ToTest.__get__('Authenticate');
    const auth = new Authenticate(config);
    auth.keycloakAdapter = {
      grantManager: {
        createGrant: () => {
          return Promise.reject(message);
        }
      }
    };
    auth.verifyAndDecodeToken('ex1123').then(result => {
      assert.equal(result, null, 'Wrong verfication result');
      done();
    }).catch(err => {
      done(err);
    });
  });
  it('Shall authenticate super user', function (done) {
    const Authenticate = ToTest.__get__('Authenticate');
    const config = {
      mqtt: {
        adminUsername: 'username',
        adminPassword: 'password'
      },
      cache: {
        port: 1432,
        host: 'cacheHost'
      }
    };
    const auth = new Authenticate(config);

    const req = {
      query: {
        username: 'username',
        password: 'password'
      }
    };
    const res = {
      status: function (status) {
        assert.equal(status, 200, 'Received wrong status');
        return this;
      },
      json: function (resultObj) {
        resultObj.should.deep.equal({ result: 'allow', is_superuser: 'false' });
        done();
      }
    };
    auth.authenticate(req, res);
  });
  it('Authentication shall successfully validate a token', function (done) {
    const decodedToken = {
      sub: 'deviceId',
      iss: 'http://keycloak-url/auth/realms/realmId',
      type: 'device',
      accounts: [{
        role: 'device',
        id: 'accountId'
      }]
    };
    const config = {
      mqtt: {
        adminUsername: 'username',
        adminPassword: 'password'
      }
    };
    const req = {
      query: {
        username: 'deviceId',
        password: 'token'
      }
    };
    const res = {
      sendStatus: function (status) {
        assert.equal(status, 400, 'Received wrong status');
        done();
      }
    };
    const Authenticate = ToTest.__get__('Authenticate');
    const auth = new Authenticate(config);
    auth.keycloakAdapter = {
      grantManager: {
        createGrant: () => {
          return Promise.resolve({
            access_token: {
              content: decodedToken
            }
          });
        }
      }
    };
    auth.verifyAndDecodeToken = function () {
      return null;
    };
    auth.authenticate(req, res);
  });
  it('Shall authenticate super user', function (done) {
    const Authenticate = ToTest.__get__('Authenticate');
    const config = {
      mqtt: {
        adminUsername: 'username',
        adminPassword: 'password'
      },
      cache: {
        port: 1432,
        host: 'cacheHost'
      }
    };
    const auth = new Authenticate(config);

    const req = {
      query: {
        username: 'username',
        password: 'password'
      }
    };
    const res = {
      status: function (status) {
        assert.equal(status, 200, 'Received wrong status');
        return this;
      },
      json: function (resultObj) {
        resultObj.should.deep.equal({ result: 'allow', is_superuser: 'false' });
        done();
      }
    };
    auth.authenticate(req, res);
  });
  it('Reject token with admin name as deviceId', function (done) {
    const decodedToken = {
      deviceId: 'username',
      iss: 'http://keycloak-url/auth/realms/realmId',
      type: 'device'
    };
    const config = {
      mqtt: {
        adminUsername: 'username',
        adminPassword: 'password'
      }
    };
    const req = {
      query: {
        username: 'username',
        password: 'token'
      }
    };
    const res = {
      sendStatus: function (status) {
        assert.equal(status, 400, 'Received wrong status');
        done();
      }
    };
    const Authenticate = ToTest.__get__('Authenticate');
    const auth = new Authenticate(config);
    auth.keycloakAdapter = {
      grantManager: {
        createGrant: () => {
          return Promise.resolve({
            access_token: {
              content: decodedToken
            }
          });
        }
      }
    };
    auth.verifyAndDecodeToken = function () {
      return decodedToken;
    };
    auth.authenticate(req, res);
  });
  /*it('Authentication shall successfully validate a token with gatewayid', function (done) {
    const decodedToken = {
      sub: 'deviceId',
      iss: 'http://keycloak-url/auth/realms/realmId',
      gateway: 'gatewayId',
      type: 'device',
      accounts: [{
        role: 'device',
        id: 'accountId'
      }]
    };
    const config = {
      mqtt: {
        adminUsername: 'username',
        adminPassword: 'password'
      }
    };

    const req = {
      query: {
        username: 'deviceId',
        password: 'token'
      }
    };
    const res = {
      sendStatus: function (status) {
        assert.equal(status, 200, 'Received wrong status');
        done();
      }
    };
    const cache = {
      setValue: function (key, type, value) {
        console.log(key, type, value);
        assert.oneOf(key, ['accountId/deviceId', 'realmId/deviceId', 'accountId/gatewayId', 'realmId/gatewayId'], 'Wrong cache value received.');
        assert.equal(type, 'acl', 'Wrong cache value received.');
        assert.equal(value, true, 'Wrong cache value received.');
      }
    };
    const Authenticate = ToTest.__get__('Authenticate');
    const auth = new Authenticate(config);
    auth.keycloakAdapter = {
      grantManager: {
        createGrant: () => {
          return Promise.resolve({
            access_token: {
              content: decodedToken
            }
          });
        }
      }
    };
    auth.verifyAndDecodeToken = function () { return decodedToken; };
    auth.authenticate(req, res);
  });*/

  it('Authentication shall detect wrong deviceId in username', function (done) {
    const decodedToken = {
      sub: 'deviceId',
      deviceId: 'deviceId',
      iss: 'http://keycloak-url/auth/realms/realmId',
      type: 'device'
    };

    const config = {
      mqtt: {
        adminUsername: 'username',
        adminPassword: 'password'
      }
    };
    const req = {
      query: {
        username: 'wrongDeviceId',
        password: 'password'
      }
    };
    const res = {
      sendStatus: function (status) {
        assert.equal(status, 400, 'Received wrong status');
        done();
      }
    };
    const cache = {
      setValue: function (key, type, value) {
        assert.oneOf(key, ['accountId/deviceId', 'realmId/deviceId'], 'Wrong cache value received.');
        assert.equal(type, 'acl', 'Wrong cache value received.');
        assert.equal(value, true, 'Wrong cache value received.');
      }
    };
    const Authenticate = ToTest.__get__('Authenticate');
    const auth = new Authenticate(config);
    auth.keycloakAdapter = {
      grantManager: {
        createGrant: () => {
          return Promise.resolve({
            access_token: {
              content: decodedToken
            }
          });
        }
      }
    };

    auth.authenticate(req, res);
  });
 /* it('Authentication shall detect wrong role in token', function (done) {
    const decodedToken = {
      sub: 'deviceId',
      iss: 'http://keycloak-url/auth/realms/realmId',
      type: 'device',
      accounts: [{
        role: 'wrontRole',
        id: 'accountId'
      }]
    };

    const config = {
      broker: {
        username: 'username',
        password: 'password'
      }
    };
    const logger = {
      debug: function () { },
      info: function () { }
    };
    const req = {
      query: {
        username: 'deviceId',
        password: 'token'
      }
    };
    const res = {
      sendStatus: function (status) {
        assert.equal(status, 400, 'Received wrong status');
        done();
      }
    };
    const cache = {
      setValue: function (key, type, value) {
        assert.oneOf(key, ['accountId/deviceId', 'realmId/deviceId'], 'Wrong cache value received.');
        assert.equal(type, 'acl', 'Wrong cache value received.');
        assert.equal(value, true, 'Wrong cache value received.');
      }
    };
    const keycloakAdapter = {
      grantManager: {
        createGrant: () => {
          return Promise.resolve({
            access_token: {
              content: decodedToken
            }
          });
        }
      }
    };

    const authenticate = new ToTest(config, logger);
    const me = ToTest.__get__('me');
    me.cache = cache;
    me.keycloakAdapter = keycloakAdapter;
    authenticate.authenticate(req, res);
  });
  it('Authentication shall detect wrong account array', function (done) {
    const decodedToken = {
      sub: 'deviceId',
      iss: 'http://keycloak-url/auth/realms/realmId',
      type: 'device',
      accounts: [{
        role: 'device',
        id: 'accountId'
      }, {
        role: 'device',
        id: 'accountId2'
      }]
    };

    const config = {
      broker: {
        username: 'username',
        password: 'password'
      }
    };
    const logger = {
      debug: function () { },
      info: function () { }
    };
    const req = {
      query: {
        username: 'deviceId',
        password: 'token'
      }
    };
    const res = {
      sendStatus: function (status) {
        assert.equal(status, 400, 'Received wrong status');
        done();
      }
    };
    const cache = {
      setValue: function (key, type, value) {
        assert.oneOf(key, ['accountId/deviceId', 'realmId/deviceId'], 'Wrong cache value received.');
        assert.equal(type, 'acl', 'Wrong cache value received.');
        assert.equal(value, true, 'Wrong cache value received.');
      }
    };
    const keycloakAdapter = {
      grantManager: {
        createGrant: () => {
          return Promise.resolve({
            access_token: {
              content: decodedToken
            }
          });
        }
      }
    };

    const authenticate = new ToTest(config, logger);
    const me = ToTest.__get__('me');
    me.cache = cache;
    me.keycloakAdapter = keycloakAdapter;
    authenticate.authenticate(req, res);
  });*/
});

fileToTest = '../lib/authService/acl.js';

describe(fileToTest, function () {
  const ToTest = rewire(fileToTest);
  class Logger {
    info () {}
    debug () {}
  };
  class Cache {};
  ToTest.__set__('Logger', Logger);
  ToTest.__set__('Cache', Cache);
  it('Shall give access control to superuser', function (done) {

    const config = {
      mqtt: {
        adminUsername: 'superuser',
        adminPassword: 'password'
      }
    };

    const Acl = ToTest.__get__('Acl');
    const acl = new Acl(config);
    const req = {
      query: {
        username: 'superuser',
        topic: 'topic'
      }
    };
    const res = {
      sendStatus: function (status) {
        assert.equal(status, 200, 'Received wrong status');
        done();
      }
    };
    acl.acl(req, res);
  });

  it('Shall give access control to SparkPlugB device DBIRTH', function (done) {
    const Cache = class Acl {
      constructor () {

      }

      getValue (subtopic, key) {
        assert.equal(aidSlashDid, subtopic, 'Wrong accountId/did subtopic');
        assert.equal(key, 'acl', 'Wrong key value');
        return true;
      }
    };
    class CacheFactory {
      constructor () {
      }

      getInstance () {
        return new Cache();
      }
    }
    const aidSlashDid = 'accountId/deviceId';

    ToTest.__set__('CacheFactory', CacheFactory);
    const config = {
      broker: {
        username: 'username',
        password: 'password'
      }
    };
    const logger = {
      debug: function () { },
      info: function () { }
    };
    const acl = new ToTest(config, logger);
    const req = {
      query: {
        username: 'deviceId',
        topic: 'spBv1.0/accountId/DBIRTH/eonID/deviceId'
      }
    };
    const res = {
      sendStatus: function (status) {
        assert.equal(status, 200, 'Received wrong status');
        done();
      }
    };
    acl.acl(req, res);
  });

  it('Shall give access control to SparkPlugB device DDATA', function (done) {
    const Cache = class Acl {
      constructor () {

      }

      getValue (subtopic, key) {
        assert.equal(aidSlashDid, subtopic, 'Wrong accountId/did subtopic');
        assert.equal(key, 'acl', 'Wrong key value');
        return true;
      }
    };
    class CacheFactory {
      constructor () {
      }

      getInstance () {
        return new Cache();
      }
    }
    const aidSlashDid = 'accountId/deviceId';

    ToTest.__set__('CacheFactory', CacheFactory);
    const config = {
      broker: {
        username: 'username',
        password: 'password'
      }
    };
    const logger = {
      debug: function () { },
      info: function () { }
    };
    const acl = new ToTest(config, logger);
    const req = {
      query: {
        username: 'deviceId',
        topic: 'spBv1.0/accountId/DDATA/eonID/deviceId'
      }
    };
    const res = {
      sendStatus: function (status) {
        assert.equal(status, 200, 'Received wrong status');
        done();
      }
    };
    acl.acl(req, res);
  });

  it('Shall give access control to SparkPlugB device NBIRTH', function (done) {
    const Cache = class Acl {
      constructor () {

      }

      getValue (subtopic, key) {
        assert.equal(aidSlashNid, subtopic, 'Wrong accountId/Gatewayid subtopic');
        assert.equal(key, 'acl', 'Wrong key value');
        return true;
      }
    };
    class CacheFactory {
      constructor () {
      }

      getInstance () {
        return new Cache();
      }
    }
    const aidSlashNid = 'accountId/gatewayId';

    ToTest.__set__('CacheFactory', CacheFactory);
    const config = {
      broker: {
        username: 'username',
        password: 'password'
      }
    };
    const logger = {
      debug: function () { },
      info: function () { }
    };
    const acl = new ToTest(config, logger);
    const req = {
      query: {
        username: 'deviceId',
        topic: 'spBv1.0/accountId/NBIRTH/gatewayId'
      }
    };
    const res = {
      sendStatus: function (status) {
        assert.equal(status, 200, 'Received wrong status');
        done();
      }
    };
    acl.acl(req, res);
  });

  it('Shall give access control to SparkPlugB device NCMD', function (done) {
    const Cache = class Acl {
      constructor () {

      }

      getValue (subtopic, key) {
        assert.equal(aidSlashNid, subtopic, 'Wrong accountId/gatewayid subtopic');
        assert.equal(key, 'acl', 'Wrong key value');
        return true;
      }
    };
    class CacheFactory {
      constructor () {
      }

      getInstance () {
        return new Cache();
      }
    }
    const aidSlashNid = 'accountId/gatewayId';

    ToTest.__set__('CacheFactory', CacheFactory);
    const config = {
      broker: {
        username: 'username',
        password: 'password'
      }
    };
    const logger = {
      debug: function () { },
      info: function () { }
    };
    const acl = new ToTest(config, logger);
    const req = {
      query: {
        username: 'deviceId',
        topic: 'spBv1.0/accountId/NCMD/gatewayId'
      }
    };
    const res = {
      sendStatus: function (status) {
        assert.equal(status, 200, 'Received wrong status');
        done();
      }
    };
    acl.acl(req, res);
  });

  it('Shall give access control to device', function (done) {
    const Cache = class Acl {
      constructor () {

      }

      getValue (subtopic, key) {
        assert.equal(aidSlashDid, subtopic, 'Wrong accountId/did subtopic');
        assert.equal(key, 'acl', 'Wrong key value');
        return true;
      }
    };
    class CacheFactory {
      constructor () {
      }

      getInstance () {
        return new Cache();
      }
    }
    const aidSlashDid = 'accountId/deviceId';

    ToTest.__set__('CacheFactory', CacheFactory);
    const config = {
      broker: {
        username: 'username',
        password: 'password'
      },
      topics: {
        prefix: 'server'
      }
    };
    const logger = {
      debug: function () { },
      info: function () { }
    };
    const acl = new ToTest(config, logger);
    const req = {
      query: {
        username: 'deviceId',
        topic: '/server/metric/' + aidSlashDid,
        access: PUBLISH
      }
    };
    const res = {
      sendStatus: function (status) {
        assert.equal(status, 200, 'Received wrong status');
        done();
      }
    };
    acl.acl(req, res);
  });
  it('Shall deny access control to device with wrong access', function (done) {
    const Cache = class Acl {
      constructor () {

      }

      getValue (subtopic, key) {
        assert.equal(aidSlashDid, subtopic, 'Wrong accountId/did subtopic');
        assert.equal(key, 'acl', 'Wrong key value');
        return true;
      }
    };
    class CacheFactory {
      constructor () {
      }

      getInstance () {
        return new Cache();
      }
    }

    const aidSlashDid = 'accountId/deviceId';

    ToTest.__set__('CacheFactory', CacheFactory);
    const config = {
      broker: {
        username: 'username',
        password: 'password'
      },
      topics: {
        prefix: 'server'
      }
    };
    const logger = {
      debug: function () { },
      info: function () { }
    };
    const acl = new ToTest(config, logger);
    const req = {
      query: {
        username: 'deviceId',
        topic: 'server/accountId/DCMD/gatewayId/deviceId',
        access: PUBLISH
      }
    };
    const res = {
      sendStatus: function (status) {
        assert.equal(status, 400, 'Received wrong status');
        done();
      }
    };
    acl.acl(req, res);
  });
  it('Shall deny access control to device with wrong topic', function (done) {
    const Cache = class Acl {
      constructor () {

      }

      getValue (subtopic, key) {
        assert.equal(key, 'acl', 'Wrong key value');
        return false;
      }
    };
    class CacheFactory {
      constructor () {
      }

      getInstance () {
        return new Cache();
      }
    }
    ToTest.__set__('CacheFactory', CacheFactory);
    const config = {
      broker: {
        username: 'username',
        password: 'password'
      },
      topics: {
        prefix: 'server'
      }
    };
    const logger = {
      debug: function () { },
      info: function () { }
    };
    const acl = new ToTest(config, logger);
    const req = {
      query: {
        username: 'deviceId',
        topic: '/server/metric/' + 'wrongtopic'
      }
    };
    const res = {
      sendStatus: function (status) {
        assert.equal(status, 400, 'Received wrong status');
        done();
      }
    };
    acl.acl(req, res);
  });
});
