<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="2.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
  xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
  xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
  xmlns:number="urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0"
  xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" 
  xmlns:chart="urn:oasis:names:tc:opendocument:xmlns:chart:1.0" 
  xmlns:dr3d="urn:oasis:names:tc:opendocument:xmlns:dr3d:1.0" 
  xmlns:math="http://www.w3.org/1998/Math/MathML" 
  xmlns:form="urn:oasis:names:tc:opendocument:xmlns:form:1.0" 
  xmlns:script="urn:oasis:names:tc:opendocument:xmlns:script:1.0" 
  xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0" 
  xmlns:ooo="http://openoffice.org/2004/office" 
  xmlns:ooow="http://openoffice.org/2004/writer" 
  xmlns:oooc="http://openoffice.org/2004/calc" 
  xmlns:dom="http://www.w3.org/2001/xml-events" 
  xmlns:xforms="http://www.w3.org/2002/xforms" 
  xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
  xmlns:rpt="http://openoffice.org/2005/report" 
  xmlns:of="urn:oasis:names:tc:opendocument:xmlns:of:1.2" 
  xmlns:xhtml="http://www.w3.org/1999/xhtml" 
  xmlns:grddl="http://www.w3.org/2003/g/data-view#" 
  xmlns:officeooo="http://openoffice.org/2009/office" 
  xmlns:tableooo="http://openoffice.org/2009/table" 
  xmlns:drawooo="http://openoffice.org/2010/draw" 
  xmlns:calcext="urn:org:documentfoundation:names:experimental:calc:xmlns:calcext:1.0" 
  xmlns:loext="urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0" 
  xmlns:field="urn:openoffice:names:experimental:ooo-ms-interop:xmlns:field:1.0" 
  xmlns:formx="urn:openoffice:names:experimental:ooxml-odf-interop:xmlns:form:1.0" 
  xmlns:css3t="http://www.w3.org/TR/css3-text/"		
  exclude-result-prefixes="">

<xsl:key name="secondary_children" match="text:p[@text:style-name =
'Index 2']"
use="generate-id(preceding-sibling::text:p[@text:style-name = 'Index
1'][1])"/>
    
<xsl:template match="text:alphabetical-index-mark-start">
    <text:alphabetical-index-mark-start>
    <xsl:attribute name="indexName">
   		<xsl:if test="not(@text:key1)">
   			<xsl:text>Index</xsl:text>
   		</xsl:if>
   		<xsl:if test="@text:key1"><xsl:value-of select="@text:key1"/></xsl:if>
   		<xsl:if test="@text:key2">:<xsl:value-of select="@text:key2"/></xsl:if>
   		<xsl:if test="@text:key3">:<xsl:value-of select="@text:key3"/></xsl:if>
   	</xsl:attribute>
    <key1><xsl:value-of select="text:alphabetical-index-mark-start"/></key1>
    </text:alphabetical-index-mark-start>
  </xsl:template>

<xsl:template match="text:alphabetical-index-mark-end"/>

<xsl:template match="text:alphabetical-index-mark">
<xsl:variable name="index-mark"><xsl:value-of select="@text:key1"/></xsl:variable>    
<xsl:variable name="charDelimiter"><xsl:text>:</xsl:text></xsl:variable>  

<xsl:choose>
  <!-- marqueurs saisie DOCX : @text:string-value is empty -->
  <xsl:when test="@text:string-value=' '">
    <text:alphabetical-index-mark>
      <xsl:attribute name="indexName">
        <xsl:choose>
          <xsl:when test="contains($index-mark,':')">
              <xsl:variable name="last">
                  <xsl:call-template name="substring-after-last">
                      <xsl:with-param name="string" select="$index-mark"/>
                      <xsl:with-param name="delimiter" select="$charDelimiter"/>
                  </xsl:call-template>
              </xsl:variable>
              <xsl:variable name="concatSep"><xsl:value-of select="concat(':',$last)"/></xsl:variable>
              <xsl:value-of select="substring-before($index-mark,$concatSep)"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>Index</xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:attribute>
        <key1>
            <xsl:variable name="term">
                  <xsl:call-template name="substring-after-last">
                      <xsl:with-param name="string" select="$index-mark"/>
                      <xsl:with-param name="delimiter" select="$charDelimiter"/>
                  </xsl:call-template>
              </xsl:variable>
              <xsl:value-of select="$term"/>
        </key1>
        <!--xsl:comment>docx</xsl:comment-->
      </text:alphabetical-index-mark>
  </xsl:when>
  <!-- marqueurs saisie DOC : @text:string-value = term -->
  <xsl:otherwise>
    <text:alphabetical-index-mark>
      <xsl:attribute name="indexName">
        <xsl:if test="not(@text:key1)"><xsl:text>Index</xsl:text></xsl:if><xsl:if test="@text:key1"><xsl:value-of select="@text:key1"/></xsl:if><xsl:if test="@text:key2">:<xsl:value-of select="@text:key2"/></xsl:if><xsl:if test="@text:key3">:<xsl:value-of select="@text:key3"/></xsl:if>
      </xsl:attribute>
      <!--xsl:comment>doc</xsl:comment-->
      <key1>
        <xsl:value-of select="@text:string-value"/>
      </key1>
    </text:alphabetical-index-mark>
  </xsl:otherwise>
</xsl:choose>
</xsl:template>

<xsl:template name="substring-after-last">
  <xsl:param name="string" />
  <xsl:param name="delimiter" />
  <xsl:choose>
    <xsl:when test="contains($string, $delimiter)">
      <xsl:call-template name="substring-after-last">
        <xsl:with-param name="string" select="substring-after($string, $delimiter)" />
        <xsl:with-param name="delimiter" select="$delimiter" />
      </xsl:call-template>
    </xsl:when>
    <xsl:otherwise>
      <xsl:value-of select="$string" />
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="substring-before-last">
  <xsl:param name="string" />
  <xsl:param name="delimiter" />
  <xsl:choose>
    <xsl:when test="contains($string, $delimiter)">
      <xsl:call-template name="substring-before-last">
        <xsl:with-param name="string" select="substring-before($string, $delimiter)" />
        <xsl:with-param name="delimiter" select="$delimiter" />
      </xsl:call-template>
    </xsl:when>
    <xsl:otherwise>
      <xsl:value-of select="$string" />
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template match="text:alphabetical-index">
    <xsl:element name="index">
      <xsl:element name="title">
        <xsl:value-of select="text:index-body/text:index-title/text:p"/>
      </xsl:element>
      <xsl:apply-templates select="text:index-body"/>
    </xsl:element>
</xsl:template>

<xsl:template match="text:index-body">
    <xsl:for-each select="text:p[@text:style-name = 'Index 1']">
      <xsl:element name="indexentry">
        <xsl:element name="primaryie">
          <xsl:value-of select="."/>
        </xsl:element>
        <xsl:if test="key('secondary_children', generate-id())">
          <xsl:element name="secondaryie">
            <xsl:value-of select="key('secondary_children', generate-id())"/>
          </xsl:element>
        </xsl:if>
      </xsl:element>
    </xsl:for-each>
</xsl:template>
    
<!-- Traitements des entrées d'index Open Office -->
<xsl:template match="text:user-index-mark-start">
	<text:user-index-mark-start indexName="{@text:index-name}">
		<key1>
			<xsl:value-of select="following-sibling::node()"/>
		</key1>
	</text:user-index-mark-start>
	<xsl:apply-templates/>
</xsl:template>

<xsl:template match="text:user-index-mark-end"/>


</xsl:stylesheet>
